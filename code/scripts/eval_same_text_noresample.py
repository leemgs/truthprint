#!/usr/bin/env python3
"""Same-text control without Truthprint's resampling (a lower bound; no new generation).

In the committed same-text run the Truthprint arm draws up to four samples and
keeps the first whose core6 record reads back, while the token watermarks get a
single sample. This script scores Truthprint on its FIRST sample only, the same
budget as the baselines:

* a sentence accepted at the first draw keeps its stored (first) text;
* a sentence with no valid draw stored its first sample, which is scored as is;
* a sentence accepted at draw 2-4 did not store its first sample; it is counted
  as a failure. The result is therefore a lower bound on single-sample
  attribution.

Attribution follows ``eval_same_text.py``: id-free search over the registered
core6 records of the 30 documents, a document attributed when >= 50% of its
sentences hit it.

Usage: python3 scripts/eval_same_text_noresample.py ../paper/results/realmt_b2 \
           ../paper/results/same_text --out ../paper/results/same_text_noresample
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint.multilingual import extract_invariants  # noqa: E402
from truthprint.provenance import CONTRACTS  # noqa: E402
from truthprint.stats import wilson_ci  # noqa: E402

CORE6 = CONTRACTS["core6"]


def record(inv: dict) -> tuple:
    return tuple(inv.get(f) for f in CORE6)


def _jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def evaluate(folder: Path, work: Path) -> dict:
    gens = [g for g in _jsonl(work / "generations.jsonl") if g["variant"] == "none"]
    usable = {g["sent_id"]: (g["tries"] == 1 and g["valid"]) or not g["valid"] for g in gens}
    used = {g["sent_id"] for g in gens}
    gold, docs = {}, defaultdict(list)
    for r in _jsonl(folder / "01_source_items.jsonl"):
        for f in r["facts"]:
            if f["sent_id"] in used:
                gold[f["sent_id"]] = record(f)
                docs[r["doc_id"]].append(f["sent_id"])
    text = {("clean", g["sent_id"]): g["text"] for g in gens}
    for t in _jsonl(work / "translations.jsonl"):
        if t["variant"] == "none":
            text[(t["condition"], t["sent_id"])] = t["text"]
    conds = ["clean"] + sorted({c for c, _ in text if c != "clean"}, key=["ko", "ar", "de"].index)
    index = defaultdict(set)
    for d, sids in docs.items():
        for sid in sids:
            index[gold[sid]].add(d)
    out = {"sentences": len(gens), "first_sample_unavailable": sum(not u for u in usable.values()),
           "conditions": {}}
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
    L = ["# Same-text control, Truthprint on its first sample only (lower bound)", "",
         f"{r['sentences']} sentences; {r['first_sample_unavailable']} were accepted at draw 2-4, their "
         "first sample was not stored, and they count as failures. Same budget as the token "
         "watermarks (one sample). Wilson 95% CI.", "",
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
    args = ap.parse_args()
    r = evaluate(Path(args.folder), Path(args.work))
    md = render(r)
    if args.out:
        Path(args.out + ".json").write_text(json.dumps(r, indent=2), encoding="utf-8")
        Path(args.out + ".md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
