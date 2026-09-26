#!/usr/bin/env python3
"""Score the wide-coverage neural invariant extractor (review W5).

Consumes ``neural_parser_outputs.jsonl`` produced by the W5 notebook: one record
per sentence with the gold invariant fields and the neural extractor's
prediction. Reports, with Wilson 95% CIs:

  * per-field recovery (pred == gold) and all-exact recovery, aggregate and per
    condition;
  * a lexicon-vs-neural head-to-head -- the scorer runs the in-repo lexicon
    extractor on the same text, so the two frontends are compared on identical
    inputs. This is the decisive measurement for W5: does the neural parser
    match the lexicon on the closed domain *and* generalize to open-domain
    wording where the lexicon abstains?

Record schema (JSONL):
    {"sent_id": "...", "lang": "ko", "condition": "ko", "domain": "template",
     "text": "<translated sentence>",
     "gold": {<9 FIELDS>}, "pred": {<9 FIELDS from the neural model>}}

Usage:
    python3 scripts/eval_neural_parser.py neural_parser_outputs.jsonl [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint.multilingual import FIELDS, extract_invariants
from truthprint.neural_parser import normalize_fields
from truthprint.stats import wilson_ci


def _read_jsonl(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _match(a, b) -> bool:
    """Field-value equality after canonical normalization."""
    if a is None or b is None:
        return a == b
    return str(a).strip().lower() == str(b).strip().lower()


def score(records: list[dict]) -> dict:
    # counters: [frontend][field] -> [hits, n]; also all-exact and per-condition
    hits = {fe: {f: [0, 0] for f in FIELDS} for fe in ("neural", "lexicon")}
    allx = {fe: [0, 0] for fe in ("neural", "lexicon")}
    per_cond = defaultdict(lambda: {fe: [0, 0] for fe in ("neural", "lexicon")})
    domains = defaultdict(lambda: {fe: [0, 0] for fe in ("neural", "lexicon")})

    for r in records:
        gold = normalize_fields(r["gold"])
        preds = {"neural": normalize_fields(r.get("pred", {}))}
        # run the in-repo lexicon extractor on the same text for head-to-head
        lang = r.get("lang", "en")
        try:
            preds["lexicon"] = normalize_fields(extract_invariants(r["text"], lang))
        except Exception:
            preds["lexicon"] = {f: None for f in FIELDS}
        cond = r.get("condition", lang)
        dom = r.get("domain", "unknown")
        for fe, pred in preds.items():
            exact = True
            for f in FIELDS:
                ok = _match(pred[f], gold[f])
                hits[fe][f][0] += int(ok)
                hits[fe][f][1] += 1
                per_cond[cond][fe][0] += int(ok)  # accumulate field-level
                per_cond[cond][fe][1] += 1
                domains[dom][fe][0] += int(ok)
                domains[dom][fe][1] += 1
                exact = exact and ok
            allx[fe][0] += int(exact)
            allx[fe][1] += 1

    def ci(pair):
        return wilson_ci(pair[0], pair[1]) if pair[1] else None

    out = {"n_records": len(records), "fields": {}, "all_exact": {}, "by_condition": {},
           "by_domain": {}}
    for fe in ("neural", "lexicon"):
        out["fields"][fe] = {f: ci(hits[fe][f]) for f in FIELDS}
        out["all_exact"][fe] = ci(allx[fe])
    for cond, d in per_cond.items():
        out["by_condition"][cond] = {fe: ci(d[fe]) for fe in ("neural", "lexicon")}
    for dom, d in domains.items():
        out["by_domain"][dom] = {fe: ci(d[fe]) for fe in ("neural", "lexicon")}
    return out


def _fmt_md(out: dict) -> str:
    lines = [
        "# Neural vs lexicon invariant extractor on real MT (W5)",
        "",
        f"{out['n_records']} sentences. Field recovery = prediction equals gold "
        "after canonical normalization (Wilson 95% CI). The lexicon column is the "
        "in-repo Stage-2 extractor run on the same text, so the neural frontend is "
        "measured head-to-head against it.",
        "",
        "## Per-field recovery",
        "",
        "| Field | Neural | Lexicon |",
        "|---|---|---|",
    ]
    for f in FIELDS:
        n = out["fields"]["neural"][f]
        l = out["fields"]["lexicon"][f]
        lines.append(f"| {f} | {n[0]:.3f} [{n[1]:.3f},{n[2]:.3f}] | "
                     f"{l[0]:.3f} [{l[1]:.3f},{l[2]:.3f}] |")
    ax_n, ax_l = out["all_exact"]["neural"], out["all_exact"]["lexicon"]
    lines += [
        f"| **all-exact** | **{ax_n[0]:.3f}** [{ax_n[1]:.3f},{ax_n[2]:.3f}] | "
        f"**{ax_l[0]:.3f}** [{ax_l[1]:.3f},{ax_l[2]:.3f}] |",
        "",
        "## By domain (field-level recovery)",
        "",
        "| Domain | Neural | Lexicon |",
        "|---|---|---|",
    ]
    for dom, d in out["by_domain"].items():
        n, l = d["neural"], d["lexicon"]
        lines.append(f"| {dom} | {n[0]:.3f} [{n[1]:.3f},{n[2]:.3f}] | "
                     f"{l[0]:.3f} [{l[1]:.3f},{l[2]:.3f}] |")
    lines += [
        "",
        "The decisive W5 result is the `open` (or non-template) domain row: the "
        "lexicon abstains or misreads out-of-vocabulary wording, so a neural "
        "frontend that holds up there is the wide-coverage parser the paper "
        "listed as the next step.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("outputs", help="neural_parser_outputs.jsonl")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    records = _read_jsonl(Path(args.outputs))
    out = score(records)
    md = _fmt_md(out)
    print(md)
    if args.out:
        d = Path(args.out)
        d.mkdir(parents=True, exist_ok=True)
        (d / "neural_parser.json").write_text(json.dumps(out, indent=2),
                                              encoding="utf-8")
        (d / "neural_parser.md").write_text(md, encoding="utf-8")
        print(f"[wrote] {d/'neural_parser.json'} and {d/'neural_parser.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
