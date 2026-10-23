#!/usr/bin/env python3
"""Build the anonymized supplementary artifact for the ACL submission.

The public repository identifies the author (repository URL, CITATION file,
author block of the IEEE/Nature sources, review notes). This script never
modifies the repository: it copies an allow-list of git-tracked files into a
fresh directory, scrubs repository URLs, writes an anonymous README and paper
Makefile, refuses to finish if any identifying string survives, and zips the
result.

Usage:
    python3 tools/make_anonymous_artifact.py [--out dist/truthprint-anonymous-artifact.zip]
                                             [--keep-dir DIR] [--self-test]
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOP = "truthprint-artifact"

# Allow-list of git-tracked paths (fnmatch patterns, matched against the repo path).
INCLUDE = [
    "code/*",
    "paper/results/*",
    "paper/acl_main.tex", "paper/references.bib", "paper/acl.sty", "paper/acl_natbib.bst",
    "paper/tools/ink_audit.py", "paper/tools/check_refs.py",
    "handoff/*.ipynb", "handoff/schemas/*", "handoff/samples/*", "handoff/validate_handoff.py",
]
EXCLUDE = [
    "code/CITATION.cff",          # names the repository owner
    "*_KO.md",                    # Korean-language working notes
    "handoff/Truthprint_Handoff_Colab.ipynb",    # generic hand-off notebooks,
    "handoff/Truthprint_Handoff_Kaggle.ipynb",   # not used by any paper result
    "*/__pycache__/*", "*.pyc",
]

# Identifying strings: the build fails if any of these survive (case-insensitive).
FORBIDDEN = [r"leemgs", r"geunsik", r"gmail\.com", r"independent researcher",
             r"\blim,\s*g\b", r"/home/user", r"claude-0", r"scratchpad"]

ANON_URL = "<ANONYMIZED-REPOSITORY-URL>"
SCRUB = [
    # badge / homepage lines are dropped entirely
    (re.compile(r"^.*actions/workflows/ci\.yml/badge\.svg.*\n", re.M), ""),
    (re.compile(r"^(Homepage|Repository) = \"https://github\.com/leemgs/truthprint\"\n", re.M), ""),
    (re.compile(r"https://colab\.research\.google\.com/github/leemgs/truthprint/blob/main/"), ANON_URL + "/"),
    (re.compile(r"https://raw\.githubusercontent\.com/leemgs/truthprint/main/"), ANON_URL + "/"),
    (re.compile(r"https://github\.com/leemgs/truthprint(\.git)?"), ANON_URL),
    # workflow wording in the hand-off tooling
    (re.compile(r"before sending it to Claude"), "before running the evaluation"),
    (re.compile(r"\(provided by Claude; "), "(provided with the artifact; "),
    (re.compile(r"hand this folder to Claude"), "run the evaluation scripts on this folder"),
]
HANGUL = re.compile("[\uac00-\ud7a3]")

# The notebook that produced the committed NLLB run has Korean instructions and
# comments (no Korean data); the artifact carries them in English.
NOTEBOOK_EN = {
    "다국어 의미기반 실측": "multilingual meaning-layer measurement",
    "**사람 주석 불필요.** 소스 생성 → NLLB로 5개 언어(+round-trip) 번역 → eval 실행 → zip.":
        "**No human annotation needed.** Generate sources → translate into 5 languages (+ round trip) with NLLB → run the evaluation → zip.",
    "셀을 위에서부터 실행하세요.": "Run the cells from the top.",
    "오른쪽 Settings → **Internet: On** (모델 다운로드 필요). Accelerator는":
        "Settings (right) → **Internet: On** (needed to download the model). As accelerator,",
    "None(CPU)로 충분하며, GPU가 있으면 번역이 더 빠릅니다.": "None (CPU) is enough; a GPU makes translation faster.",
    "## 셀 1 — 환경 감지 + 클론 + 설치": "## Cell 1 — detect environment, clone, install",
    "git clone 실패 -> 인터넷(Internet: On)을 확인하세요.": "git clone failed -> check that Internet is On.",
    "## 셀 2 — 실제-규모 영어 소스 생성 (문서 수 조절 가능)": "## Cell 2 — generate the English sources (number of documents adjustable)",
    "# 문서↑ = 신뢰구간(CI)↑. 50 권장(GPU면 ~5분). 파일럿은 10.": "# more documents = tighter CIs; 50 recommended (~5 min on a GPU); pilot: 10.",
    "## 셀 3 — NLLB로 5개 언어 + round-trip 번역 (실제 MT, GPU 자동/배치)":
        "## Cell 3 — translate into 5 languages + round trip with NLLB (real MT, GPU used automatically, batched)",
    "모델 최초 다운로드는 약 2.4GB(1회). **GPU가 있으면 자동 사용**되어 훨씬 빠릅니다.":
        "The first model download is about 2.4 GB (once). **A GPU is used automatically** if present and is much faster.",
    "(Kaggle: 오른쪽 Settings → Accelerator → **GPU T4 x2** 권장. 없으면 CPU로도 동작.)":
        "(Kaggle: Settings → Accelerator → **GPU T4 x2** recommended; CPU also works.)",
    "# 대상 언어(추가/삭제 가능)": "# target languages (add or remove)",
    "# GPU면 그대로, CPU 메모리 부족 시 8로 낮추세요.": "# keep on a GPU; lower to 8 if CPU memory is short.",
    "## 셀 4 — 실측 실행 (필드 복원율 + 의미기반 provenance 인증)":
        "## Cell 4 — run the measurement (field recovery + meaning-based provenance authentication)",
    "두 표가 이 데이터의 정직한 실측입니다(ko/hi/zh/ar/de/round-trip).":
        "The two tables are the measurement on this data (ko/hi/zh/ar/de/round trip).",
    "## 셀 5 — 결과 zip 만들기 → 나에게 전달": "## Cell 5 — package the results as a zip",
    "아래 링크 클릭해 다운로드 (Kaggle/로컬):": "Click the link below to download (Kaggle/local):",
    "수동 다운로드 경로:": "Manual download path:",
    "Kaggle이면 오른쪽 파일 패널에서 b2_results.zip 우클릭 -> Download 도 가능합니다.":
        "On Kaggle you can also right-click b2_results.zip in the file panel -> Download.",
}

README = """# Truthprint — anonymized supplementary artifact

Code, committed data and result files for the anonymous ACL 2027 submission
*Truthprint: Typed Invariant Contracts for Translation-Robust Authenticated
Semantic Provenance*. Every number of the paper's Truthprint results recomputes
on a CPU from the files here.

## Contents

| Path | What |
|---|---|
| `code/` | Python package `truthprint` (extractors, provenance scheme, coding layer), evaluation scripts in `code/scripts/`, tests |
| `paper/results/` | Committed result files and the raw real-MT run (`realmt_b2/`: 50 source documents x 16 sentences, 4,800 NLLB-200-distilled-600M translations) |
| `paper/acl_main.tex` | Paper source (anonymous); `make -C paper` builds `acl_main.pdf` |
| `handoff/` | GPU notebooks used to produce the translations, the token-watermark (KGW) baseline and the cached neural extractions; schemas and samples |

Repository URLs in the notebooks were replaced by `<ANONYMIZED-REPOSITORY-URL>`;
upload this folder instead of cloning.

## Reproduce

```bash
cd code && pip install -e ".[dev]" && pytest -q          # unit and consistency tests
python3 -m truthprint.cli selftest                         # P1-P4, L1-L3, 0/20,000 tag acceptances
cd code
python3 scripts/eval_multilingual.py ../paper/results/realmt_b2          # Stage-2 field recovery
python3 scripts/eval_provenance.py   ../paper/results/realmt_b2          # authentication by contract
python3 scripts/eval_ledger_search.py ../paper/results/realmt_b2         # verification without an identifier
python3 scripts/eval_ledger_scale.py ../paper/results/realmt_b2 --validate   # ledgers up to 100,050 documents
python3 scripts/eval_handoff.py      ../paper/results/realmt_b2 --objective   # surface-carrier parse coverage
pip install model2vec   # optional embedding backend for the baselines below
python3 scripts/eval_semantic_baselines.py --b2 ../paper/results/realmt_b2   # matched-FPR comparison (Table 1)
pip install sentence-transformers   # optional paraphrase-tuned encoder (Table 1, rows marked *)
python3 scripts/eval_semantic_baselines.py --b2 ../paper/results/realmt_b2 --model st:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
python3 scripts/eval_same_text.py ../paper/results/realmt_b2 --docs 30 --work ../paper/results/same_text --stage score   # same-text KGW/SynthID-Text vs Truthprint (cached generations)
python3 scripts/eval_retrieval.py --real-embedding                       # retrieval / NLI baselines
```

The token-watermark baseline (KGW on GPT-2) requires a GPU
(`handoff/Truthprint_W4_Baselines_Kaggle.ipynb`); its raw detector scores are not
included.
"""

MAKEFILE = """.PHONY: all audit clean

all:
\tpdflatex -interaction=nonstopmode -halt-on-error acl_main.tex
\tbibtex acl_main
\tpdflatex -interaction=nonstopmode -halt-on-error acl_main.tex
\tpdflatex -interaction=nonstopmode -halt-on-error acl_main.tex

audit: all
\tpython3 tools/ink_audit.py acl_main.pdf

clean:
\trm -f *.aux *.log *.out *.bbl *.blg acl_main.pdf
"""


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True,
                         capture_output=True, text=True).stdout.splitlines()
    keep = []
    for f in out:
        if any(fnmatch.fnmatch(f, p) for p in EXCLUDE):
            continue
        if any(fnmatch.fnmatch(f, p) for p in INCLUDE):
            keep.append(f)
    return keep


def is_text(data: bytes) -> bool:
    return b"\0" not in data[:4096]


def build(dest: Path) -> list[str]:
    files = tracked_files()
    for f in files:
        src, dst = ROOT / f, dest / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        if is_text(data):
            text = data.decode("utf-8")
            for pat, rep in SCRUB:
                text = pat.sub(rep, text)
            if f.endswith(".ipynb"):
                for ko, en in NOTEBOOK_EN.items():
                    text = text.replace(ko, en)
            dst.write_text(text, encoding="utf-8")
        else:
            dst.write_bytes(data)
    (dest / "README.md").write_text(README, encoding="utf-8")
    (dest / "paper" / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    return files


def leaks(dest: Path) -> list[str]:
    rx = re.compile("|".join(FORBIDDEN + [r"\bclaude\b"]), re.I)
    found = []
    for p in sorted(dest.rglob("*")):
        if p.is_file():
            data = p.read_bytes().decode("utf-8", "replace")
            for m in rx.finditer(data):
                line = data.count("\n", 0, m.start()) + 1
                found.append(f"{p.relative_to(dest)}:{line}: {m.group(0)!r}")
            # Korean is an evaluation language (data, lexicon, tests); only prose
            # documents must not carry Korean-language working notes.
            h = HANGUL.search(data) if p.suffix in (".md", ".ipynb") else None
            if h:
                found.append(f"{p.relative_to(dest)}: Korean text {h.group(0)!r}")
    return found


def self_test(dest: Path) -> None:
    """The artifact must build the paper and pass its tests on its own."""
    subprocess.run(["make", "-C", "paper", "all"], cwd=dest, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log = (dest / "paper" / "acl_main.log").read_text(errors="replace")
    bad = [l for l in log.splitlines() if re.search(r"Overfull|Float too large|undefined", l)]
    if bad:
        raise SystemExit("paper build warnings in artifact:\n" + "\n".join(bad[:10]))
    r = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=dest / "code",
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("tests failed in artifact:\n" + r.stdout[-2000:])
    print("[self-test] paper builds cleanly;", r.stdout.strip().splitlines()[-1])
    for junk in ("acl_main.aux", "acl_main.log", "acl_main.out", "acl_main.bbl",
                 "acl_main.blg", "acl_main.pdf"):
        (dest / "paper" / junk).unlink(missing_ok=True)
    for cache in dest.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    for egg in dest.rglob("*.egg-info"):
        shutil.rmtree(egg, ignore_errors=True)
    shutil.rmtree(dest / "code" / ".pytest_cache", ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist" / "truthprint-anonymous-artifact.zip"))
    ap.add_argument("--keep-dir", default=None, help="also leave the unpacked tree here")
    ap.add_argument("--self-test", action="store_true",
                    help="build the paper and run the tests inside the artifact")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / TOP
        files = build(dest)
        found = leaks(dest)
        if found:
            print("identifying strings remain; artifact NOT written:", *found, sep="\n  ")
            return 1
        if args.self_test:
            self_test(dest)
            found = leaks(dest)
            if found:
                print("identifying strings after self-test:", *found, sep="\n  ")
                return 1
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(dest.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(dest.parent))
        if args.keep_dir:
            shutil.copytree(dest, Path(args.keep_dir) / TOP, dirs_exist_ok=True)
        size = out.stat().st_size / 1e6
        print(f"[written] {out} ({len(files)} repository files + README + Makefile, {size:.1f} MB); "
              "no identifying strings found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
