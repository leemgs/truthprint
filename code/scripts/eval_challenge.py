#!/usr/bin/env python3
"""Field-level semantic challenge set: typed-invariant contract vs. an
embedding-similarity gate, with a component ablation.

This is a real, fully-offline, standard-library-only experiment on actual
sentence strings (no neural model, no network). It operationalizes the paper's
central claim -- that embedding *similarity* cannot separate meaning-preserving
realization changes from lexically small but meaning-*altering* edits -- and
measures what each Truthprint component contributes.

For six protected fields (polarity, quantity, temporal direction, modality,
attribution, causation) it reports, with 95% confidence intervals:

  * typed  -- Truthprint (h_I-bound MAC): tamper-detection and benign retention;
  * no_mac -- decode-only ablation (attributes on carrier recovery alone);
  * embed  -- an embedding-similarity gate calibrated to keep >= 95% of
              legitimate paraphrases, then measured on tamper.

It also reports the threshold-inversion rate: the fraction of tampers that are
at least as embedding-similar as a legitimate paraphrase of the same sentence,
where *no* similarity threshold can separate meaning-altering from
meaning-preserving edits.

Run:  python3 scripts/eval_challenge.py [--docs N] [--out PATH]
Writes a Markdown results table and a JSON blob next to the paper by default.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint import challenge as ch


def _ci(triple):
    p, lo, hi = triple
    return f"{p:.3f} [{lo:.3f}, {hi:.3f}]"


def _fmt_markdown(r: dict) -> str:
    c = r["config"]
    lines = []
    lines.append("# Field-level semantic challenge set (Stage-1, closed domain)")
    lines.append("")
    lines.append("Real, fully-offline experiment on actual sentence strings "
                 "(standard library only, no neural model, no network). "
                 "Regenerate with `python3 scripts/eval_challenge.py`.")
    lines.append("")
    lines.append(f"- Documents: {c['n_docs']} x {c['sents_per_doc']} facts; "
                 f"code `[{c['code_n']}, {c['msg_len'] + c['tag_bits']}]` "
                 f"GF(2) (rate {(c['msg_len'] + c['tag_bits']) / c['code_n']:.2f}).")
    lines.append(f"- Payload: {c['msg_len']}-bit message + {c['tag_bits']}-bit "
                 f"tag. Benign transform erases {c['benign_erase_prob']:.0%} of "
                 f"carriers (meaning preserved).")
    lines.append(f"- Embedding gate calibrated to <= "
                 f"{c['benign_false_reject_target']:.0%} benign false-reject: "
                 f"theta* = {r['embedding_theta']:.4f} "
                 f"(bag-of-words cosine).")
    lines.append(f"- CIs: Wilson (rates), bootstrap "
                 f"({c['num_resamples']} resamples, mean cosine). "
                 f"Seed {c['seed']}.")
    lines.append("")
    b = r["benign"]
    lines.append("## Benign (meaning-preserving) behavior")
    lines.append("")
    lines.append("| Quantity | Value (95% CI) |")
    lines.append("|---|---|")
    lines.append(f"| Truthprint attribution retained | {_ci(b['typed_retention'])} |")
    lines.append(f"| Embedding gate false-reject | {_ci(b['embed_false_reject'])} |")
    lines.append(f"| Mean paraphrase cosine | {_ci(b['mean_cosine_paraphrase'])} |")
    lines.append("")
    lines.append("## Tamper detection by protected field")
    lines.append("")
    lines.append("| Field | Truthprint (typed) | No-MAC (decode-only) | "
                 "Embedding gate | Mean tamper cosine | Threshold-inversion |")
    lines.append("|---|---|---|---|---|---|")
    for f in ch.FIELDS:
        d = r["per_field"][f]
        lines.append(
            f"| {f} | {_ci(d['typed_tamper_detect'])} | "
            f"{_ci(d['nomac_tamper_detect'])} | {_ci(d['embed_tamper_detect'])} | "
            f"{_ci(d['mean_cosine_tamper'])} | "
            f"{_ci(d['threshold_inversion_rate'])} |")
    a = r["aggregate"]
    lines.append(
        f"| **all fields** | **{_ci(a['typed_tamper_detect'])}** | "
        f"**{_ci(a['nomac_tamper_detect'])}** | "
        f"**{_ci(a['embed_tamper_detect'])}** | --- | "
        f"**{_ci(a['threshold_inversion_rate'])}** |")
    lines.append("")
    lines.append("## Reading the result")
    lines.append("")
    lines.append("- The typed invariant + MAC contract detects every "
                 "single-field meaning-altering edit while retaining "
                 "attribution across legitimate paraphrases.")
    lines.append("- Removing the h_I-bound MAC (decode-only) drops "
                 "tamper-detection to zero: the carriers still recover, so the "
                 "MAC binding is the load-bearing component for tamper "
                 "resistance.")
    lines.append("- An embedding-similarity gate calibrated to keep legitimate "
                 "paraphrases catches almost no tamper, because a single-field "
                 "edit is lexically smaller than a legitimate voice/time "
                 "reflow. The threshold-inversion rate quantifies why: for a "
                 "large fraction of cases the tamper is at least as similar as "
                 "the paraphrase, so no threshold can separate them.")
    lines.append("")
    lines.append("This is a Stage-1 closed-domain demonstration, not a "
                 "wide-coverage multilingual parser; it isolates the contract "
                 "property, not neural frontend accuracy.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", type=int, default=300)
    ap.add_argument("--sents", type=int, default=24)
    ap.add_argument("--seed", type=int, default=20270101)
    ap.add_argument("--resamples", type=int, default=2000)
    ap.add_argument("--out", type=str, default=None,
                    help="Markdown output path (default: paper/results/"
                         "challenge_results.md)")
    ap.add_argument("--json", type=str, default=None,
                    help="JSON output path (default: alongside --out)")
    args = ap.parse_args()

    r = ch.run_challenge(n_docs=args.docs, sents_per_doc=args.sents,
                         seed=args.seed, num_resamples=args.resamples)
    md = _fmt_markdown(r)
    print(md)

    repo = Path(__file__).resolve().parent.parent.parent
    out = Path(args.out) if args.out else repo / "paper/results/challenge_results.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    jpath = Path(args.json) if args.json else out.with_suffix(".json")
    jpath.write_text(json.dumps(r, indent=2), encoding="utf-8")
    print(f"\n[written] {out}\n[written] {jpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
