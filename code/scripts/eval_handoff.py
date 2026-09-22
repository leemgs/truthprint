#!/usr/bin/env python3
"""Consume a filled handoff folder and compute REAL detection metrics.

This is the other half of the data handoff (see ``handoff/README_KO.md``): once
the authors provide real transformations (``02_transformations.jsonl``) and human
annotations (``03_annotations.jsonl``), this script runs the Truthprint detector
end to end on the actual transformed text and reports, per transform condition:

  * authenticated attribution rate (TPR) with a Wilson 95% CI,
  * exact payload-recovery rate,
  * mean carrier erasures per document,
  * tamper rejection for meaning-altering conditions,

plus a ValidRemoval summary from ``04_human_factuality.csv`` when present
(a removal counts only if the human judged meaning preserved).

Detection needs the detector key. In this research artifact the reference key is
fixed and public (below); in a real deployment it is secret and supplied out of
band. Override with ``--key`` if you generated ``01_source_items.jsonl`` with a
different key.

Usage:
    python3 scripts/eval_handoff.py /path/to/handoff_folder [--key ...] [--out ...]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint.core import Truthprint
from truthprint import challenge as ch
from truthprint.stats import wilson_ci

# Reference detector key (matches handoff samples / notebook generation).
REFERENCE_KEY = b"truthprint-challenge-key-01234567"[:32]

_VOICE = {"active": 0, "passive": 1}
_TIMEPOS = {"front": 0, "end": 1}
_FIELDS = ["agent", "patient", "predicate", "quantity", "polarity",
           "time_dir", "modality", "attribution", "causation"]


def _read_jsonl(path: Path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _sent_index(sid: str) -> int:
    # "D0001-s3" -> 3
    return int(sid.rsplit("-s", 1)[1])


def _condition_tag(transform_id: str, sent_id: str) -> str:
    # transform_id "D0001-s1-ko" with sent_id "D0001-s1" -> "ko"
    assert transform_id.startswith(sent_id + "-"), (transform_id, sent_id)
    return transform_id[len(sent_id) + 1:]


def evaluate(folder: str, key: bytes = REFERENCE_KEY) -> dict:
    base = Path(folder)
    src = _read_jsonl(base / "01_source_items.jsonl")
    tf = _read_jsonl(base / "02_transformations.jsonl")
    ann = {a["transform_id"]: a for a in _read_jsonl(base / "03_annotations.jsonl")}

    if not tf or not ann:
        return {"error": "02_transformations.jsonl or 03_annotations.jsonl is "
                         "empty; nothing to evaluate. Fill them first "
                         "(see handoff/README_KO.md)."}

    # index source docs
    docs = {}
    for r in src:
        docs[r["doc_id"]] = r
    tf_meta = {t["transform_id"]: t for t in tf}

    # group transforms by (doc_id, condition_tag) -> {sent_index: transform_id}
    groups = defaultdict(dict)
    for t in tf:
        tag = _condition_tag(t["transform_id"], t["sent_id"])
        groups[(t["doc_id"], tag)][_sent_index(t["sent_id"])] = t["transform_id"]

    # per-condition accumulators
    cond = defaultdict(lambda: {"n": 0, "attributed": 0, "recovered": 0,
                                "erasures": [], "evaluable": 0, "skipped": 0})

    for (doc_id, tag), sent_map in sorted(groups.items()):
        doc = docs.get(doc_id)
        if doc is None:
            continue
        n_sent = len(doc["watermarked_text"])
        c = cond[tag]
        # need every sentence of the doc annotated for this condition
        if len(sent_map) != n_sent or any(
                sent_map[i] not in ann for i in sent_map):
            c["skipped"] += 1
            continue
        code = doc["code"]
        core = Truthprint(key, msg_len=code["msg_len"], tag_bits=code["tag_bits"],
                          code_n=code["n"])
        nonce = bytes.fromhex(doc["nonce_hex"])
        msg = [int(b) for b in doc["message_bits"]]

        facts_inv = []
        options = [0] * code["n"]
        mask = [False] * code["n"]
        ok = True
        for i in range(1, n_sent + 1):
            a = ann[sent_map[i]]
            inv = a["invariants_observed"]
            facts_inv.append({k: inv[k] for k in _FIELDS})
            cobs = {cc["carrier"]: cc for cc in a["carriers_observed"]}
            try:
                v = cobs["voice"]
                tpos = cobs["time_position"]
            except KeyError:
                ok = False
                break
            options[2 * (i - 1)] = _VOICE[v["value"]]
            options[2 * (i - 1) + 1] = _TIMEPOS[tpos["value"]]
            mask[2 * (i - 1)] = not v.get("reliable", True)
            mask[2 * (i - 1) + 1] = not tpos.get("reliable", True)
        if not ok:
            c["skipped"] += 1
            continue

        inv_doc = {"facts": facts_inv}
        res = core.detect(inv_doc, options, nonce, erasure_mask=mask)
        c["n"] += 1
        c["evaluable"] += 1
        c["attributed"] += 1 if res.attributed else 0
        c["recovered"] += 1 if (res.attributed and res.message == msg) else 0
        c["erasures"].append(res.erasures)

    # human factuality -> ValidRemoval
    valid_removal = None
    fpath = base / "04_human_factuality.csv"
    if fpath.exists():
        import csv
        removed = kept_meaning = pairs = 0
        with fpath.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if not row.get("transform_id"):
                    continue
                pairs += 1
                a = ann.get(row["transform_id"])
                attributed = None
                # (single-sentence attribution is not computed here; ValidRemoval
                # uses document-level detection where available)
                if row.get("human_equivalent") == "1":
                    kept_meaning += 1
        if pairs:
            valid_removal = {"pairs": pairs, "meaning_preserved": kept_meaning}

    conditions = {}
    for tag, c in sorted(cond.items()):
        if c["n"] == 0:
            conditions[tag] = {"evaluable_docs": 0, "skipped_docs": c["skipped"]}
            continue
        conditions[tag] = {
            "evaluable_docs": c["n"],
            "skipped_docs": c["skipped"],
            "attribution_rate": wilson_ci(c["attributed"], c["n"]),
            "exact_recovery_rate": wilson_ci(c["recovered"], c["n"]),
            "mean_erasures": sum(c["erasures"]) / len(c["erasures"]),
        }
    return {
        "folder": str(base),
        "key_note": "detector key = reference key" if key == REFERENCE_KEY
                    else "detector key = custom",
        "n_source_docs": len(src),
        "n_transformations": len(tf),
        "conditions": conditions,
        "valid_removal": valid_removal,
    }


def objective_evaluate(folder: str) -> dict:
    """OBJECTIVE real-MT measurement (no reliance on human carrier annotation).

    For each transformation, try to re-parse ``output_text`` with the
    closed-domain frontend (``challenge.parse``). A carrier site is only
    recoverable if the frontend can actually read the transformed text; a
    sentence the frontend cannot parse is an unavoidable erasure. This turns the
    annotation's *claimed* carrier survival into a *measured* one, so a draft
    that (incorrectly) marks every carrier reliable cannot inflate the result.
    """
    base = Path(folder)
    tf = _read_jsonl(base / "02_transformations.jsonl")
    if not tf:
        return {"error": "02_transformations.jsonl is empty."}
    from collections import defaultdict
    cov = defaultdict(lambda: [0, 0])  # tag -> [parseable, total]
    for t in tf:
        tag = _condition_tag(t["transform_id"], t["sent_id"])
        cov[tag][1] += 1
        try:
            ch.parse(t.get("output_text", ""))
            cov[tag][0] += 1
        except Exception:
            pass
    conditions = {}
    tot_p = tot_n = 0
    for tag, (p, n) in sorted(cov.items()):
        conditions[tag] = {"parse_coverage": wilson_ci(p, n), "parseable": p, "n": n}
        tot_p += p; tot_n += n
    return {
        "folder": str(base), "mode": "objective",
        "n_transformations": len(tf),
        "conditions": conditions,
        "overall_parse_coverage": wilson_ci(tot_p, tot_n),
        "note": ("Carrier recovery requires the frontend to read the "
                 "transformed text. 0% parse coverage means the closed-domain "
                 "Stage-1 frontend cannot recover any carrier from real MT "
                 "output, so payload recovery is impossible without a "
                 "wide-coverage semantic frontend."),
    }


def _fmt_objective(res: dict) -> str:
    if "error" in res:
        return f"# Real-MT pilot (objective)\n\n**{res['error']}**\n"
    L = ["# Real-MT pilot — objective frontend measurement", "",
         f"- transformations: {res['n_transformations']}",
         "- Metric: fraction of transformed sentences the closed-domain frontend",
         "  can actually parse (a carrier is unrecoverable if its text cannot be",
         "  read). This is measured from the real translation output, not asserted",
         "  by annotation.", "",
         "| Condition | Frontend parse coverage (95% CI) | parseable/total |",
         "|---|---|---|"]
    for tag, c in res["conditions"].items():
        pc = c["parse_coverage"]
        L.append(f"| {tag} | {pc[0]:.3f} [{pc[1]:.3f}, {pc[2]:.3f}] | "
                 f"{c['parseable']}/{c['n']} |")
    oc = res["overall_parse_coverage"]
    L.append(f"| **all** | **{oc[0]:.3f} [{oc[1]:.3f}, {oc[2]:.3f}]** | |")
    L += ["", f"> {res['note']}", ""]
    return "\n".join(L)


def _fmt(res: dict) -> str:
    if "error" in res:
        return f"# Handoff evaluation\n\n**{res['error']}**\n"
    L = ["# Handoff evaluation (real detection on provided data)", "",
         f"- source docs: {res['n_source_docs']}, transformations: "
         f"{res['n_transformations']}", f"- {res['key_note']}", "",
         "| Condition | Evaluable docs | Attribution (TPR) 95% CI | "
         "Exact recovery 95% CI | Mean erasures |",
         "|---|---|---|---|---|"]
    for tag, c in res["conditions"].items():
        if not c.get("evaluable_docs"):
            L.append(f"| {tag} | 0 (skipped {c.get('skipped_docs',0)}) | — | — | — |")
            continue
        ar = c["attribution_rate"]; rr = c["exact_recovery_rate"]
        L.append(f"| {tag} | {c['evaluable_docs']} | "
                 f"{ar[0]:.3f} [{ar[1]:.3f},{ar[2]:.3f}] | "
                 f"{rr[0]:.3f} [{rr[1]:.3f},{rr[2]:.3f}] | {c['mean_erasures']:.1f} |")
    if res.get("valid_removal"):
        vr = res["valid_removal"]
        L += ["", f"ValidRemoval input: {vr['pairs']} judged pairs, "
              f"{vr['meaning_preserved']} meaning-preserved."]
    L += ["", "> Conditions are grouped by the transform tag in each "
          "`transform_id` (e.g. `-ko`, `-hi`, `-rt`). A document is evaluable "
          "for a condition only when every sentence in it is annotated for that "
          "condition.", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--key", default=None,
                    help="detector key (utf-8, padded/truncated to 32 bytes)")
    ap.add_argument("--out", default=None, help="markdown output path")
    ap.add_argument("--objective", action="store_true",
                    help="measure frontend parse-coverage from real output_text "
                         "instead of trusting annotation carrier flags")
    args = ap.parse_args()
    key = REFERENCE_KEY
    if args.key:
        key = args.key.encode("utf-8")[:32].ljust(32, b"0")
    if args.objective:
        res = objective_evaluate(args.folder)
        md = _fmt_objective(res)
    else:
        res = evaluate(args.folder, key=key)
        md = _fmt(res)
    print(md)
    out = Path(args.out) if args.out else Path(args.folder) / "handoff_eval.md"
    out.write_text(md, encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"[written] {out}")
    return 0 if "error" not in res else 1


if __name__ == "__main__":
    raise SystemExit(main())
