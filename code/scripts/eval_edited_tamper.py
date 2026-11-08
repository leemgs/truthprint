#!/usr/bin/env python3
"""Score the edited-text tamper corpus against the *original* ledger.

Each translated sentence was produced from text in which one field was edited
(``make_edited_tamper.py``). The verifier re-extracts the invariants (Stage-2)
and authenticates against the tag registered for the *unedited* source; an
acceptance is a false accept. Per edited field and contract we report

* ``accepted``  - the translated edit authenticates against the original record
                  (false accept for an in-contract field; expected for a field
                  outside the contract),
* ``reads_edit`` - the extractor reads back the edited record (core6/full9
                  projection), i.e. the rejection is because the edit was seen,
                  not because extraction failed.

Usage: python3 scripts/eval_edited_tamper.py ../paper/results/realmt_b2 \
           ../paper/results/edited_tamper [--out ../paper/results/edited_tamper_eval]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_provenance import REFERENCE_KEY, TAG_BITS, _LANG, _read_jsonl  # noqa: E402
from truthprint.multilingual import extract_invariants  # noqa: E402
from truthprint.provenance import CONTRACTS, authenticate, register_tag  # noqa: E402
from truthprint.stats import wilson_ci  # noqa: E402

NONCE = b"prov-nonce-01"
REPORTED = ["core6", "full9"]


def _gold(folder: Path, name: str) -> tuple[dict, dict]:
    gold, field = {}, {}
    for r in _read_jsonl(folder / name):
        for f in r["facts"]:
            gold[f["sent_id"]] = {k: v for k, v in f.items() if k != "sent_id"}
        field.update(r.get("edited_field", {}))
    return gold, field


def evaluate(source: str, edited: str) -> dict:
    orig, _ = _gold(Path(source), "01_source_items.jsonl")
    new, field = _gold(Path(edited), "01_edited_items.jsonl")
    tf = _read_jsonl(Path(edited) / "02_transformations.jsonl")
    out = {"sentences": len(new), "translations": len(tf), "fields": sorted(set(field.values())),
           "contracts": {}}
    for c in REPORTED:
        reg = {sid: register_tag(REFERENCE_KEY, g, NONCE, sid, c, TAG_BITS) for sid, g in orig.items()}
        acc = defaultdict(lambda: [0, 0, 0])  # (field, in_contract) -> [accepted, reads_edit, n]
        per_cond = defaultdict(lambda: [0, 0])  # cond -> [accepted in-contract, n in-contract]
        for t in tf:
            cond = t["transform_id"].rsplit("-", 1)[1]
            sid = t["sent_id"]
            obs = extract_invariants(t["output_text"], _LANG[cond])
            ok = authenticate(REFERENCE_KEY, obs, NONCE, sid, reg[sid], c, TAG_BITS)
            reads = all(obs.get(k) == new[sid].get(k) for k in CONTRACTS[c])
            fld = field[sid]
            row = acc[fld]
            row[0] += ok
            row[1] += reads
            row[2] += 1
            if fld in CONTRACTS[c]:
                per_cond[cond][0] += ok
                per_cond[cond][1] += 1
        inside = [f for f in out["fields"] if f in CONTRACTS[c]]
        outside = [f for f in out["fields"] if f not in CONTRACTS[c]]
        tot_in = [sum(acc[f][i] for f in inside) for i in range(3)]
        tot_out = [sum(acc[f][i] for f in outside) for i in range(3)]
        out["contracts"][c] = {
            "in_contract_fields": inside, "outside_contract_fields": outside,
            "per_field": {f: {"in_contract": f in CONTRACTS[c], "n": acc[f][2],
                              "accepted": wilson_ci(acc[f][0], acc[f][2]),
                              "reads_edit": wilson_ci(acc[f][1], acc[f][2])}
                          for f in out["fields"]},
            "false_accept_in_contract": wilson_ci(tot_in[0], tot_in[2]),
            "reads_edit_in_contract": wilson_ci(tot_in[1], tot_in[2]),
            "accepted_outside_contract": wilson_ci(tot_out[0], tot_out[2]) if tot_out[2] else None,
            "false_accept_by_condition": {k: wilson_ci(a, n) for k, (a, n) in sorted(per_cond.items())},
            "n_in_contract": tot_in[2], "n_outside_contract": tot_out[2],
        }
    return out


def render(r: dict) -> str:
    f = lambda t: f"{t[0]:.3f} [{t[1]:.3f},{t[2]:.3f}]"  # noqa: E731
    L = ["# Edited-text tamper under real translation", "",
         f"{r['sentences']} source sentences, each with one field edited in the text and re-realized "
         f"with the same template; {r['translations']} NLLB translations (5 languages + Korean round "
         "trip). The verifier authenticates against the tag registered for the *unedited* source "
         "(id-addressed, 32-bit keyed tag). `accepted` for an in-contract field is a false accept; "
         "`reads edit` is the share whose re-extracted record equals the edited one (the rejection "
         "is caused by seeing the edit, not by an extraction failure). Wilson 95% CI.", ""]
    for c, d in r["contracts"].items():
        L += [f"## Contract `{c}`", "",
              f"False accept over in-contract edits: **{f(d['false_accept_in_contract'])}** "
              f"(n={d['n_in_contract']}); edit read back: {f(d['reads_edit_in_contract'])}."]
        if d["accepted_outside_contract"]:
            L.append(f"Accepted when the edit is outside the contract (by design): "
                     f"{f(d['accepted_outside_contract'])} (n={d['n_outside_contract']}).")
        L += ["", "| Edited field | In contract | n | Accepted | Reads edit |", "|---|---|---|---|---|"]
        for fld, x in d["per_field"].items():
            L.append(f"| {fld} | {'yes' if x['in_contract'] else 'no'} | {x['n']} | "
                     f"{f(x['accepted'])} | {f(x['reads_edit'])} |")
        L += ["", "False accept (in-contract edits) by condition: " + "; ".join(
            f"{k} {v[0]:.3f}" for k, v in d["false_accept_by_condition"].items()), ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("edited")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    r = evaluate(args.source, args.edited)
    md = render(r)
    if args.out:
        Path(args.out + ".json").write_text(json.dumps(r, indent=2), encoding="utf-8")
        Path(args.out + ".md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
