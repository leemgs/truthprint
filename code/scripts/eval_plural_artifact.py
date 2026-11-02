#!/usr/bin/env python3
"""Does the generator's ungrammatical plural ("cache misss") bias the results?

The template generator pluralizes by appending ``s`` (``challenge.py``), so a
quantity > 1 of "cache miss" is rendered "cache misss". This script counts the
affected source sentences in the committed NLLB run and compares Stage-2
recovery between affected and unaffected sentences, per condition: the patient
field, the core6 record, and all nine fields. No new translation is run.

Usage: python3 scripts/eval_plural_artifact.py ../paper/results/realmt_b2 \
           [--out ../paper/results/plural_artifact]
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


def evaluate(folder: str) -> dict:
    base = Path(folder)
    gold, affected = {}, {}
    for d in _read_jsonl(base / "01_source_items.jsonl"):
        for f in d["facts"]:
            sid = f["sent_id"]
            gold[sid] = {k: v for k, v in f.items() if k != "sent_id"}
            if TOKEN in d["watermarked_text"][sid]:
                affected[sid] = "affected"
            elif f["quantity"] != 1:
                affected[sid] = "plural_control"  # other patients, quantity > 1 (grammatical plural)
            else:
                affected[sid] = "singular"
    acc = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0]))  # cond -> group -> [patient, core6, full9, n]
    docs = defaultdict(lambda: defaultdict(list))  # cond -> doc -> [(affected, core6 ok)]
    for t in _read_jsonl(base / "02_transformations.jsonl"):
        cond = t["transform_id"].rsplit("-", 1)[1]
        if cond not in _LANG:
            continue
        inv = extract_invariants(t["output_text"], _LANG[cond])
        g = gold[t["sent_id"]]
        row = acc[cond][affected[t["sent_id"]]]
        row[0] += inv.get("patient") == g["patient"]
        row[1] += all(inv.get(k) == g.get(k) for k in CONTRACTS["core6"])
        row[2] += all(inv.get(k) == g.get(k) for k in CONTRACTS["full9"])
        row[3] += 1
        docs[cond][t["doc_id"]].append((affected[t["sent_id"]] == "affected",
                                         all(inv.get(k) == g.get(k) for k in CONTRACTS["core6"])))
    out = {"token": TOKEN, "affected_sources": sum(v == "affected" for v in affected.values()),
           "plural_control_sources": sum(v == "plural_control" for v in affected.values()),
           "sources": len(affected),
           "conditions": {}}
    for cond in sorted(acc):
        groups = acc[cond]
        tot = [sum(groups[g][i] for g in groups) for i in range(4)]
        clean = [sum(groups[g][i] for g in groups if g != "affected") for i in range(4)]
        out.setdefault("core6_all_vs_without_affected", {})[cond] = {
            "all": wilson_ci(tot[1], tot[3]), "without_affected": wilson_ci(clean[1], clean[3])}
        # id-addressed document attribution (>= half of the sentences match the core6 record)
        def attr(keep):
            hit = 0
            for sents in docs[cond].values():
                kept = [ok for aff, ok in sents if keep(aff)]
                hit += bool(kept) and sum(kept) >= 0.5 * len(kept)
            return wilson_ci(hit, len(docs[cond]))
        out.setdefault("doc_attribution_all_vs_without_affected", {})[cond] = {
            "all": attr(lambda a: True), "without_affected": attr(lambda a: not a)}
        out["conditions"][cond] = {
            grp: {"n": r[3], "patient": wilson_ci(r[0], r[3]), "core6": wilson_ci(r[1], r[3]),
                  "full9": wilson_ci(r[2], r[3])}
            for grp, r in sorted(acc[cond].items())}
    return out


def render(r: dict) -> str:
    f = lambda t: f"{t[0]:.3f} [{t[1]:.3f},{t[2]:.3f}]"  # noqa: E731
    L = ["# Generator plural artifact (\"cache misss\")", "",
         f"{r['affected_sources']} of {r['sources']} source sentences contain the ungrammatical "
         f"plural *cache {r['token']}* (template generator appends \"s\"); they were translated as is. "
         "Stage-2 recovery on the committed NLLB outputs (Wilson 95% CI): affected sentences vs a "
         f"plural control ({r['plural_control_sources']} sources with another patient and quantity > 1, "
         "grammatical plural) and singular sentences. The affected group differs from the control "
         "only in the patient noun, so the patient noun and the misspelling are confounded.", "",
         "| Condition | Group | n | Patient | core6 record | All nine fields |", "|---|---|---|---|---|---|"]
    for cond, groups in r["conditions"].items():
        for grp, d in groups.items():
            L.append(f"| {cond} | {grp} | {d['n']} | {f(d['patient'])} | {f(d['core6'])} | {f(d['full9'])} |")
    L += ["", "core6 record recovery, all sentences vs excluding affected ones:", "",
          "| Condition | All | Without affected |", "|---|---|---|"]
    for cond, d in r["core6_all_vs_without_affected"].items():
        L.append(f"| {cond} | {f(d['all'])} | {f(d['without_affected'])} |")
    L += ["", "core6 document attribution (id-addressed, >= half of the sentences), all sentences vs "
          "excluding affected ones:", "", "| Condition | All | Without affected |", "|---|---|---|"]
    for cond, d in r["doc_attribution_all_vs_without_affected"].items():
        L.append(f"| {cond} | {f(d['all'])} | {f(d['without_affected'])} |")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    r = evaluate(args.folder)
    md = render(r)
    if args.out:
        Path(args.out + ".json").write_text(json.dumps(r, indent=2), encoding="utf-8")
        Path(args.out + ".md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
