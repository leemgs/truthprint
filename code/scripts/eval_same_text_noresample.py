#!/usr/bin/env python3
"""Same-text control without Truthprint's resampling.

In the committed same-text run the Truthprint arm draws up to four samples and
keeps the first whose core6 record reads back, while the token watermarks get a
single sample. This script scores Truthprint on its FIRST sample only, the same
budget as the baselines:

* a sentence accepted at the first draw keeps its stored (first) text;
* a sentence with no valid draw stored its first sample, which is scored as is;
* a sentence accepted at draw 2-4 is scored on its first sample when the run
  stored it (``first_text``, translated here by the same NLLB settings into
  ``first_translations.jsonl``, stage ``--translate``); without it the sentence
  counts as a failure and the result is a lower bound.

Attribution follows ``eval_same_text.py``: id-free search over the registered
core6 records of the 30 documents, a document attributed when >= 50% of its
sentences hit it.

Usage: python3 scripts/eval_same_text_noresample.py ../paper/results/realmt_b2 \
           ../paper/results/same_text [--translate] --out ../paper/results/same_text_noresample
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from truthprint.multilingual import extract_invariants  # noqa: E402
from truthprint.provenance import CONTRACTS  # noqa: E402
from truthprint.stats import wilson_ci  # noqa: E402

CORE6 = CONTRACTS["core6"]


def record(inv: dict) -> tuple:
    return tuple(inv.get(f) for f in CORE6)


def _jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _redrawn(gens: list[dict]) -> list[dict]:
    """Sentences whose kept text is not their first sample."""
    return [g for g in gens if g["variant"] == "none" and g.get("first_text") is not None
            and g["first_text"] != g["text"]]


def translate_first(work: Path, conds: list[str]) -> None:
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    from eval_same_text import MT_MODEL, NLLB  # same translator and language codes
    todo = _redrawn(_jsonl(work / "generations.jsonl"))
    torch.set_num_threads(4)
    tok = AutoTokenizer.from_pretrained(MT_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(MT_MODEL).eval()
    tok.src_lang = NLLB["en"]
    rows = []
    for c in conds:
        for i in range(0, len(todo), 16):
            batch = todo[i:i + 16]
            enc = tok([g["first_text"] for g in batch], return_tensors="pt", padding=True,
                      truncation=True, max_length=128)
            with torch.no_grad():
                ids = model.generate(**enc, forced_bos_token_id=tok.convert_tokens_to_ids(NLLB[c]),
                                     max_length=160)
            rows += [{"sent_id": g["sent_id"], "condition": c, "text": t}
                     for g, t in zip(batch, tok.batch_decode(ids, skip_special_tokens=True))]
    (work / "first_translations.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def evaluate(folder: Path, work: Path) -> dict:
    allgens = _jsonl(work / "generations.jsonl")
    gens = [g for g in allgens if g["variant"] == "none"]
    redrawn = {g["sent_id"] for g in _redrawn(allgens)}
    ft = work / "first_translations.jsonl"
    first_tr = {(r["condition"], r["sent_id"]): r["text"] for r in _jsonl(ft)} if ft.exists() else {}
    exact = bool(redrawn) and all(("ko", s) in first_tr for s in redrawn)
    usable = {g["sent_id"]: (g["tries"] == 1 and g["valid"]) or not g["valid"] or
              (exact and g["sent_id"] in redrawn) for g in gens}
    used = {g["sent_id"] for g in gens}
    gold, docs = {}, defaultdict(list)
    for r in _jsonl(folder / "01_source_items.jsonl"):
        for f in r["facts"]:
            if f["sent_id"] in used:
                gold[f["sent_id"]] = record(f)
                docs[r["doc_id"]].append(f["sent_id"])
    text = {("clean", g["sent_id"]): g.get("first_text") or g["text"] for g in gens}
    for t in _jsonl(work / "translations.jsonl"):
        if t["variant"] == "none":
            text[(t["condition"], t["sent_id"])] = t["text"]
    if exact:
        text.update(first_tr)
    conds = ["clean"] + sorted({c for c, _ in text if c != "clean"}, key=["ko", "ar", "de"].index)
    index = defaultdict(set)
    for d, sids in docs.items():
        for sid in sids:
            index[gold[sid]].add(d)
    out = {"sentences": len(gens), "exact": exact, "redrawn": len(redrawn),
           "first_sample_unavailable": sum(not u for u in usable.values()), "conditions": {}}
    for cond in conds:
        lang = "en" if cond == "clean" else cond
        own = false_docs = ok = n = 0
        for d, sids in docs.items():
            hits = Counter()
            for sid in sids:
                n += 1
                if not usable[sid]:
                    continue
                obs = record(extract_invariants(text[(cond, sid)], lang))
                ok += obs == gold[sid]
                for doc in index.get(obs, ()):
                    hits[doc] += 1
            attributed = {doc for doc, c in hits.items() if c >= 0.5 * len(sids)}
            own += d in attributed
            false_docs += bool(attributed - {d})
        out["conditions"][cond] = {"document_attribution": wilson_ci(own, len(docs)),
                                   "sentence_authentication": wilson_ci(ok, n),
                                   "docs_with_false_attribution": wilson_ci(false_docs, len(docs))}
    return out


def render(r: dict) -> str:
    f = lambda t: f"{t[0]:.3f} [{t[1]:.3f},{t[2]:.3f}]"  # noqa: E731
    if r.get("exact"):
        head = ["# Same-text control, Truthprint on its first sample only", "",
                f"{r['sentences']} sentences; the {r['redrawn']} accepted at draw 2-4 are scored on their "
                "stored first sample, translated with the same NLLB settings. Same budget as the "
                "token watermarks (one sample). Wilson 95% CI.", ""]
    else:
        head = ["# Same-text control, Truthprint on its first sample only (lower bound)", "",
                f"{r['sentences']} sentences; {r['first_sample_unavailable']} were accepted at draw 2-4, "
                "their first sample was not stored, and they count as failures. Same budget as the "
                "token watermarks (one sample). Wilson 95% CI.", ""]
    L = head + [
         "| Condition | Document attribution | Sentence authentication | Docs w/ false attribution |",
         "|---|---|---|---|"]
    for c, d in r["conditions"].items():
        L.append(f"| {c} | {f(d['document_attribution'])} | {f(d['sentence_authentication'])} | "
                 f"{f(d['docs_with_false_attribution'])} |")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("work")
    ap.add_argument("--out", default=None)
    ap.add_argument("--translate", action="store_true",
                    help="translate the stored first samples of redrawn sentences first")
    args = ap.parse_args()
    if args.translate:
        translate_first(Path(args.work), ["ko", "ar", "de"])
    r = evaluate(Path(args.folder), Path(args.work))
    md = render(r)
    if args.out:
        Path(args.out + ".json").write_text(json.dumps(r, indent=2), encoding="utf-8")
        Path(args.out + ".md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
