#!/usr/bin/env python3
"""Fact fidelity of the same-text generations (no new generation).

Reads the committed ``same_text/generations.jsonl`` and asks, for each variant,
whether the Stage-2 extractor reads back the source sentence's core6 record from
the clean English output. This is an *extractor-based* proxy: a mismatch can be
a dropped fact or wording the lexicon does not cover; no human judged it.

Also reports the Truthprint validation loop's sampling cost (number of draws per
sentence until the record read back, capped at the try budget).

Usage: python3 scripts/eval_same_text_fidelity.py ../paper/results/realmt_b2 \
           ../paper/results/same_text --out ../paper/results/same_text_fidelity
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint.multilingual import extract_invariants  # noqa: E402
from truthprint.provenance import CONTRACTS  # noqa: E402
from truthprint.stats import wilson_ci  # noqa: E402

CORE6 = CONTRACTS["core6"]


def record(inv: dict) -> tuple:
    return tuple(inv.get(f) for f in CORE6)


def evaluate(folder: Path, work: Path) -> dict:
    gold = {}
    for line in (folder / "01_source_items.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            for f in json.loads(line)["facts"]:
                gold[f["sent_id"]] = record(f)
    gens = [json.loads(l) for l in (work / "generations.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    hits, n = Counter(), Counter()
    first_ok = 0
    tries = Counter()
    for g in gens:
        ok = record(extract_invariants(g["text"], "en")) == gold[g["sent_id"]]
        hits[g["variant"]] += ok
        n[g["variant"]] += 1
        if g["variant"] == "none":
            tries[g["tries"]] += 1
            first_ok += ok and g["tries"] == 1
    none_n = n["none"]
    return {
        "proxy": "Stage-2 extractor reads back the source core6 record (clean English)",
        "kgw": wilson_ci(hits["kgw"], n["kgw"]),
        "synthid": wilson_ci(hits["synthid"], n["synthid"]),
        "unwatermarked_first_sample": wilson_ci(first_ok, none_n),
        "truthprint_validated": wilson_ci(hits["none"], none_n),
        "sentences": none_n,
        "draws_per_sentence_mean": round(sum(k * v for k, v in tries.items()) / none_n, 4),
        "draws_histogram": {str(k): tries[k] for k in sorted(tries)},
        "no_valid_realization": none_n - hits["none"],
    }


def render(r: dict) -> str:
    f = lambda t: f"{t[0]:.3f} [{t[1]:.3f},{t[2]:.3f}]"  # noqa: E731
    return "\n".join([
        "# Same-text fact fidelity (extractor-based proxy)", "",
        f"Proxy: {r['proxy']}; {r['sentences']} sentences per variant; Wilson 95% CI. "
        "A mismatch may be a dropped fact or unread wording; no human judgment.", "",
        "| Variant | core6 read back |", "|---|---|",
        f"| Unwatermarked, first sample | {f(r['unwatermarked_first_sample'])} |",
        f"| KGW | {f(r['kgw'])} |",
        f"| SynthID-Text | {f(r['synthid'])} |",
        f"| Truthprint (validated, up to 4 draws) | {f(r['truthprint_validated'])} |", "",
        f"Truthprint draws per sentence: mean {r['draws_per_sentence_mean']:.2f}, histogram "
        f"{r['draws_histogram']}; {r['no_valid_realization']} sentences had no valid realization.", ""])


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
