#!/usr/bin/env python3
"""Did the generator's former ungrammatical plural ("cache misss") bias the results?

The legacy generator pluralized by appending ``s``, so a quantity > 1 of "cache
miss" was rendered "cache misss". The generator is fixed and the corpus was
re-translated (``scripts/make_realmt.py``). This script scores both runs on the
same sentence groups (affected / grammatical-plural control / singular): the
patient field, the core6 record, all nine fields, and core6 document attribution.

Usage: python3 scripts/eval_plural_artifact.py ../paper/results/realmt_b2_legacy \
           ../paper/results/realmt_b2 [--out ../paper/results/plural_artifact]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_provenance import _LANG, _read_jsonl  # noqa: E402
from truthprint.multilingual import extract_invariants  # noqa: E402
from truthprint.provenance import CONTRACTS  # noqa: E402
from truthprint.stats import wilson_ci  # noqa: E402

TOKEN = "misss"


def _run(folder: Path, groups: dict) -> dict:
    gold = {}
    for d in _read_jsonl(folder / "01_source_items.jsonl"):
        for f in d["facts"]:
            gold[f["sent_id"]] = {k: v for k, v in f.items() if k != "sent_id"}
    acc = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0]))  # cond -> group -> [patient, core6, full9, n]
    docs = defaultdict(lambda: defaultdict(list))  # cond -> doc -> [(affected, core6 ok)]
    for t in _read_jsonl(folder / "02_transformations.jsonl"):
        cond = t["transform_id"].rsplit("-", 1)[1]
        if cond not in _LANG:
            continue
        inv = extract_invariants(t["output_text"], _LANG[cond])
        g, grp = gold[t["sent_id"]], groups[t["sent_id"]]
        ok6 = all(inv.get(k) == g.get(k) for k in CONTRACTS["core6"])
        row = acc[cond][grp]
        row[0] += inv.get("patient") == g["patient"]
        row[1] += ok6
        row[2] += all(inv.get(k) == g.get(k) for k in CONTRACTS["full9"])
        row[3] += 1
        docs[cond][t["doc_id"]].append((grp == "affected", ok6))
    out = {"conditions": {}, "core6_all_vs_without_affected": {},
           "doc_attribution_all_vs_without_affected": {}}
    for cond in sorted(acc):
        grp_rows = acc[cond]
        tot = [sum(grp_rows[g][i] for g in grp_rows) for i in range(4)]
        clean = [sum(grp_rows[g][i] for g in grp_rows if g != "affected") for i in range(4)]
        out["core6_all_vs_without_affected"][cond] = {
            "all": wilson_ci(tot[1], tot[3]), "without_affected": wilson_ci(clean[1], clean[3])}

        # id-addressed document attribution (>= half of the sentences match the core6 record)
        def attr(keep):
            hit = 0
            for sents in docs[cond].values():
                kept = [ok for aff, ok in sents if keep(aff)]
                hit += bool(kept) and sum(kept) >= 0.5 * len(kept)
            return wilson_ci(hit, len(docs[cond]))
        out["doc_attribution_all_vs_without_affected"][cond] = {
            "all": attr(lambda a: True), "without_affected": attr(lambda a: not a)}
        out["conditions"][cond] = {
            grp: {"n": r[3], "patient": wilson_ci(r[0], r[3]), "core6": wilson_ci(r[1], r[3]),
                  "full9": wilson_ci(r[2], r[3])}
            for grp, r in sorted(grp_rows.items())}
    return out


def evaluate(legacy: str, fixed: str) -> dict:
    """Group sentences by the *legacy* source text and score both runs on the same groups."""
    groups = {}
    for d in _read_jsonl(Path(legacy) / "01_source_items.jsonl"):
        for f in d["facts"]:
            sid = f["sent_id"]
            if TOKEN in d["watermarked_text"][sid]:
                groups[sid] = "affected"
            elif f["quantity"] != 1:
                groups[sid] = "plural_control"  # other patients, quantity > 1 (grammatical plural)
            else:
                groups[sid] = "singular"
    fixed_src = {sid: t for d in _read_jsonl(Path(fixed) / "01_source_items.jsonl")
                 for sid, t in d["watermarked_text"].items()}
    legacy_src = {sid: t for d in _read_jsonl(Path(legacy) / "01_source_items.jsonl")
                  for sid, t in d["watermarked_text"].items()}
    changed = sorted(sid for sid in fixed_src if fixed_src[sid] != legacy_src[sid])
    return {"token": TOKEN, "affected_sources": sum(v == "affected" for v in groups.values()),
            "plural_control_sources": sum(v == "plural_control" for v in groups.values()),
            "sources": len(groups),
            "changed_sources_in_fixed_run": len(changed),
            "changed_equals_affected": changed == sorted(s for s, v in groups.items() if v == "affected"),
            "fixed_contains_token": any(TOKEN in t for t in fixed_src.values()),
            "legacy": _run(Path(legacy), groups), "fixed": _run(Path(fixed), groups)}


def render(r: dict) -> str:
    f = lambda t: f"{t[0]:.3f} [{t[1]:.3f},{t[2]:.3f}]"  # noqa: E731
    L = ["# Generator plural artifact (\"cache misss\"): legacy vs corrected corpus", "",
         f"The legacy generator appended \"s\" to form plurals, so {r['affected_sources']} of "
         f"{r['sources']} source sentences contained *cache {r['token']}*. The corrected generator "
         f"changes exactly {r['changed_sources_in_fixed_run']} sources (same as the affected set: "
         f"{r['changed_equals_affected']}); all {r['sources']} sources were re-translated with the same "
         "NLLB system (`scripts/make_realmt.py`). Groups are defined on the legacy text: affected, a "
         f"plural control ({r['plural_control_sources']} sources with another patient and quantity > 1) "
         "and singular sentences. Stage-2 recovery, Wilson 95% CI.", ""]
    for run in ("legacy", "fixed"):
        L += [f"## {run} corpus", "", "| Condition | Group | n | Patient | core6 record | All nine fields |",
              "|---|---|---|---|---|---|"]
        for cond, groups in r[run]["conditions"].items():
            for grp, d in groups.items():
                L.append(f"| {cond} | {grp} | {d['n']} | {f(d['patient'])} | {f(d['core6'])} | {f(d['full9'])} |")
        L.append("")
    L += ["## core6 sentence recovery and document attribution (all sentences)", "",
          "| Condition | Sentence, legacy | Sentence, corrected | Document, legacy | Document, corrected |",
          "|---|---|---|---|---|"]
    for cond in r["fixed"]["core6_all_vs_without_affected"]:
        L.append(f"| {cond} | {f(r['legacy']['core6_all_vs_without_affected'][cond]['all'])} | "
                 f"{f(r['fixed']['core6_all_vs_without_affected'][cond]['all'])} | "
                 f"{f(r['legacy']['doc_attribution_all_vs_without_affected'][cond]['all'])} | "
                 f"{f(r['fixed']['doc_attribution_all_vs_without_affected'][cond]['all'])} |")
    L += ["", "Document attribution excluding the affected sentences (legacy / corrected): " + "; ".join(
        f"{c} {r['legacy']['doc_attribution_all_vs_without_affected'][c]['without_affected'][0]:.3f}/"
        f"{r['fixed']['doc_attribution_all_vs_without_affected'][c]['without_affected'][0]:.3f}"
        for c in r["fixed"]["doc_attribution_all_vs_without_affected"]), ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("legacy")
    ap.add_argument("fixed")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    r = evaluate(args.legacy, args.fixed)
    md = render(r)
    if args.out:
        Path(args.out + ".json").write_text(json.dumps(r, indent=2), encoding="utf-8")
        Path(args.out + ".md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
