#!/usr/bin/env python3
"""Score a real head-to-head baseline comparison on real-MT output (review W4).

The diagnostic simulator (``scripts/eval_baselines.py``, paper Appendix A) is
explicitly *not* a benchmark and must not rank methods. This scorer instead
consumes **real detector outputs** produced by official/self-contained baseline
implementations on the *same* watermark -> real-NLLB-translation pipeline used
for Truthprint, and builds an apples-to-apples comparison at a common operating
point.

It reads ``05_baseline_outputs.jsonl`` (schema in ``handoff/W4_SCHEMA_KO.md``),
one record per (method, unit, condition, watermarked?) with a detector
``score``. For each method it calibrates a decision threshold at a target FPR
on the null (``watermarked=false``) population, then reports, per condition:

  * TPR at the target FPR (Wilson 95% CI);
  * ROC-AUC (Mann--Whitney; bootstrap 95% CI) from watermarked-vs-null scores.

If a Truthprint provenance results file is given (``--truthprint``), its
meaning-digest sentence-level TPR / document attribution are merged into the
same table so the token- and embedding-level baselines can be read next to the
meaning-layer method at their respective measured operating points.

Usage:
    python3 scripts/eval_baselines_real.py 05_baseline_outputs.jsonl \\
        [--truthprint paper/results/provenance_realmt.json] \\
        [--fpr 0.01] [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint.stats import wilson_ci

# Canonical condition order for the comparison table.
CONDITIONS = ["clean", "rt", "ko", "hi", "zh", "ar", "de"]
COND_LABEL = {"clean": "clean", "rt": "EN round-trip", "ko": "EN->KO",
              "hi": "EN->HI", "zh": "EN->ZH", "ar": "EN->AR", "de": "EN->DE"}


def _read_jsonl(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _threshold_at_fpr(null_scores: list[float], fpr: float) -> float:
    """Smallest threshold t such that P(null >= t) <= fpr.

    Uses the (1-fpr) empirical quantile of the null scores; ties resolved
    conservatively by scanning candidate cut points.
    """
    if not null_scores:
        return float("inf")
    s = sorted(null_scores)
    n = len(s)
    # candidate thresholds are just-above each observed null score, plus +inf
    best = float("inf")
    for cut in s + [float("inf")]:
        # decision: score > cut  (strictly greater avoids counting the cut itself)
        fp = sum(1 for x in s if x > cut)
        if fp / n <= fpr:
            best = cut
            break
    return best


def _auc(pos: list[float], neg: list[float]) -> float:
    """Mann--Whitney U / |pos||neg| = P(pos > neg) with 0.5 ties."""
    if not pos or not neg:
        return float("nan")
    wins = 0.0
    for a in pos:
        for b in neg:
            if a > b:
                wins += 1.0
            elif a == b:
                wins += 0.5
    return wins / (len(pos) * len(neg))


def _auc_bootstrap_ci(pos, neg, resamples=1000, seed=13):
    if not pos or not neg:
        return (float("nan"), float("nan"), float("nan"))
    rng = random.Random(seed)
    point = _auc(pos, neg)
    boot = []
    for _ in range(resamples):
        p = [pos[rng.randrange(len(pos))] for _ in pos]
        q = [neg[rng.randrange(len(neg))] for _ in neg]
        boot.append(_auc(p, q))
    boot.sort()
    lo = boot[int(0.025 * len(boot))]
    hi = boot[int(0.975 * len(boot)) - 1]
    return (point, lo, hi)


def score(records: list[dict], fpr: float = 0.01) -> dict:
    by_method = defaultdict(list)
    for r in records:
        by_method[r["method"]].append(r)

    out = {"target_fpr": fpr, "methods": {}}
    for method, recs in by_method.items():
        null_scores = [float(r["score"]) for r in recs if not r["watermarked"]]
        thr = _threshold_at_fpr(null_scores, fpr)
        conds = {}
        for cond in CONDITIONS:
            pos = [float(r["score"]) for r in recs
                   if r["watermarked"] and r.get("condition") == cond]
            neg = [float(r["score"]) for r in recs
                   if not r["watermarked"] and r.get("condition") == cond] or null_scores
            if not pos:
                continue
            tp = sum(1 for x in pos if x > thr)
            tpr = wilson_ci(tp, len(pos))
            auc = _auc_bootstrap_ci(pos, neg)
            conds[cond] = {"tpr_at_fpr": tpr, "n_pos": len(pos),
                           "roc_auc": auc}
        out["methods"][method] = {
            "impl": recs[0].get("impl", ""),
            "threshold": thr,
            "n_null": len(null_scores),
            "conditions": conds,
        }
    return out


def merge_truthprint(out: dict, prov_path: Path, contract: str = "core6") -> None:
    """Add Truthprint meaning-digest rows from a provenance results file."""
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    c = prov.get("contracts", {}).get(contract)
    if not c:
        return
    conds = {}
    for tag, cd in c.get("conditions", {}).items():
        # provenance uses 'rt' for round-trip; map straight through
        stpr = cd.get("sentence_tpr")
        doc = cd.get("document_attribution")
        if stpr is None:
            continue
        conds[tag] = {"tpr_at_fpr": stpr, "n_pos": cd.get("n_sent"),
                      "doc_attribution": doc, "roc_auc": None}
    out["methods"][f"Truthprint (meaning-digest, {contract})"] = {
        "impl": "meaning-digest provenance; operating FP = contract-collision "
                "floor (~5e-3 core6), not a 1% threshold",
        "threshold": None, "n_null": None, "conditions": conds,
        "note": "authentication (MAC-style), not a tunable score; shown at its "
                "own measured operating point",
    }


def _fmt_cell(cond_data: dict) -> str:
    t = cond_data.get("tpr_at_fpr")
    if not t:
        return "---"
    return f"{t[0]:.3f}"


def _fmt_md(out: dict) -> str:
    methods = list(out["methods"].keys())
    present = [c for c in CONDITIONS
               if any(c in out["methods"][m]["conditions"] for m in methods)]
    lines = [
        "# Real head-to-head baseline comparison on real MT (W4)",
        "",
        f"TPR at {out['target_fpr']*100:.0f}% FPR after real NLLB translation. "
        "Baselines calibrated per method on their null population; Truthprint "
        "shown at its own measured operating point (contract-collision floor, "
        "not a tunable threshold). This is the real-data replacement for the "
        "diagnostic simulator, which must not be used to rank methods.",
        "",
        "| Method | " + " | ".join(COND_LABEL[c] for c in present) + " |",
        "|---|" + "|".join("---" for _ in present) + "|",
    ]
    for m in methods:
        cells = []
        for c in present:
            cd = out["methods"][m]["conditions"].get(c)
            cells.append(_fmt_cell(cd) if cd else "---")
        lines.append(f"| {m} | " + " | ".join(cells) + " |")
    lines += ["", f"_Implementations:_ " + "; ".join(
        f"**{m}**: {out['methods'][m]['impl']}" for m in methods)]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline_outputs", help="05_baseline_outputs.jsonl")
    ap.add_argument("--truthprint", default=None,
                    help="provenance results JSON to merge (optional)")
    ap.add_argument("--contract", default="core6")
    ap.add_argument("--fpr", type=float, default=0.01)
    ap.add_argument("--out", default=None, help="output directory")
    args = ap.parse_args()

    records = _read_jsonl(Path(args.baseline_outputs))
    out = score(records, fpr=args.fpr)
    if args.truthprint:
        merge_truthprint(out, Path(args.truthprint), contract=args.contract)

    md = _fmt_md(out)
    print(md)
    if args.out:
        d = Path(args.out)
        d.mkdir(parents=True, exist_ok=True)
        (d / "baselines_real.json").write_text(json.dumps(out, indent=2),
                                               encoding="utf-8")
        (d / "baselines_real.md").write_text(md, encoding="utf-8")
        print(f"[wrote] {d/'baselines_real.json'} and {d/'baselines_real.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
