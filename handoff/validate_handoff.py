#!/usr/bin/env python3
"""Validate a Truthprint handoff data folder before sending it to Claude.

Usage:
    python3 handoff/validate_handoff.py handoff/samples
    python3 handoff/validate_handoff.py /path/to/your/handoff_data

Checks required fields, enum values, and cross-references between files, then
prints a readiness report. Standard library only (no install needed).

Files expected in the folder (see handoff/README_KO.md):
    01_source_items.jsonl        (provided by Claude; you translate its text)
    02_transformations.jsonl     (YOU: real MT/paraphrase/summary outputs)   [required]
    03_annotations.jsonl         (YOU: human gold invariants + carriers)      [required]
    04_human_factuality.csv      (YOU: benign/altering equivalence judgments) [recommended]
    05_baseline_outputs.jsonl    (YOU: official baseline detector outputs)    [optional]
    split.json                   (calibration/test doc ids)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

FIELDS = ["polarity", "quantity", "time_dir", "modality", "attribution",
          "causation"]
INV_ENUMS = {
    "polarity": {"positive", "negative"},
    "time_dir": {"previous", "following"},
    "modality": {"asserted", "necessary", "possible"},
    "attribution": {"none", "report", "vendor"},
    "causation": {"none", "cause", "purpose"},
}
TRANSFORM_TYPES = {"translation", "roundtrip_translation", "paraphrase",
                   "summarization", "adaptive_paraphrase", "splice", "noop"}
CARRIER_NAMES = {"voice", "time_position"}
CARRIER_VALUES = {"voice": {"active", "passive"},
                  "time_position": {"front", "end"}}


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def err(self, f, msg):
        self.errors.append(f"[ERROR] {f}: {msg}")

    def warn(self, f, msg):
        self.warnings.append(f"[warn]  {f}: {msg}")

    def note(self, msg):
        self.info.append(f"[info]  {msg}")


def _read_jsonl(path: Path, rep: Report):
    rows = []
    if not path.exists():
        return rows
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            rep.err(path.name, f"line {i}: invalid JSON ({e})")
    return rows


def _require(rep, fname, row, keys, idx):
    ok = True
    for k in keys:
        if k not in row:
            rep.err(fname, f"row {idx}: missing required field '{k}'")
            ok = False
    return ok


def validate(folder: str) -> int:
    base = Path(folder)
    rep = Report()
    if not base.is_dir():
        print(f"[ERROR] not a directory: {folder}")
        return 2

    # ---- 01 source items ---------------------------------------------------
    src = _read_jsonl(base / "01_source_items.jsonl", rep)
    src_sent_ids = set()
    src_doc_ids = set()
    for i, r in enumerate(src, 1):
        _require(rep, "01_source_items.jsonl", r,
                 ["doc_id", "nonce_hex", "message_bits", "watermarked_text"], i)
        src_doc_ids.add(r.get("doc_id"))
        for sid in (r.get("watermarked_text") or {}):
            src_sent_ids.add(sid)
    rep.note(f"01_source_items: {len(src)} docs, {len(src_sent_ids)} sentences")

    # ---- 02 transformations (required) ------------------------------------
    tf = _read_jsonl(base / "02_transformations.jsonl", rep)
    if not tf:
        rep.err("02_transformations.jsonl", "REQUIRED file is missing/empty")
    tf_ids = set()
    placeholders = 0
    for i, r in enumerate(tf, 1):
        _require(rep, "02_transformations.jsonl", r,
                 ["transform_id", "doc_id", "sent_id", "transform_type",
                  "system", "output_text"], i)
        tf_ids.add(r.get("transform_id"))
        if r.get("transform_type") not in TRANSFORM_TYPES:
            rep.err("02_transformations.jsonl",
                    f"row {i}: transform_type '{r.get('transform_type')}' "
                    f"not in {sorted(TRANSFORM_TYPES)}")
        if src_sent_ids and r.get("sent_id") not in src_sent_ids:
            rep.err("02_transformations.jsonl",
                    f"row {i}: sent_id '{r.get('sent_id')}' not in 01 source")
        sysname = str(r.get("system", ""))
        if r.get("_placeholder") or "REPLACE" in sysname:
            placeholders += 1
    if placeholders:
        rep.warn("02_transformations.jsonl",
                 f"{placeholders} rows are still PLACEHOLDERS "
                 "(system contains 'REPLACE' or _placeholder=true). "
                 "Replace output_text with real MT output and set real system.")

    # ---- 03 annotations (required) ----------------------------------------
    ann = _read_jsonl(base / "03_annotations.jsonl", rep)
    if not ann:
        rep.err("03_annotations.jsonl", "REQUIRED file is missing/empty")
    ann_tf = set()
    for i, r in enumerate(ann, 1):
        _require(rep, "03_annotations.jsonl", r,
                 ["transform_id", "annotator_id", "invariants_observed",
                  "carriers_observed", "invariant_preserved"], i)
        ann_tf.add(r.get("transform_id"))
        if tf_ids and r.get("transform_id") not in tf_ids:
            rep.err("03_annotations.jsonl",
                    f"row {i}: transform_id '{r.get('transform_id')}' "
                    "has no matching row in 02_transformations")
        inv = r.get("invariants_observed") or {}
        for f in FIELDS:
            if f not in inv:
                rep.err("03_annotations.jsonl",
                        f"row {i}: invariants_observed missing '{f}'")
            elif f in INV_ENUMS and inv.get(f) not in INV_ENUMS[f]:
                rep.err("03_annotations.jsonl",
                        f"row {i}: {f}='{inv.get(f)}' not in "
                        f"{sorted(INV_ENUMS[f])}")
        for c in (r.get("carriers_observed") or []):
            if c.get("carrier") not in CARRIER_NAMES:
                rep.err("03_annotations.jsonl",
                        f"row {i}: carrier '{c.get('carrier')}' not in "
                        f"{sorted(CARRIER_NAMES)}")
            elif c.get("value") not in CARRIER_VALUES[c["carrier"]]:
                rep.err("03_annotations.jsonl",
                        f"row {i}: {c['carrier']} value '{c.get('value')}' "
                        f"not in {sorted(CARRIER_VALUES[c['carrier']])}")
            if not isinstance(c.get("reliable"), bool):
                rep.err("03_annotations.jsonl",
                        f"row {i}: carrier 'reliable' must be true/false")

    # every transformation should be annotated
    missing_ann = tf_ids - ann_tf
    if missing_ann:
        rep.warn("03_annotations.jsonl",
                 f"{len(missing_ann)} transformations have no annotation: "
                 f"{sorted(missing_ann)[:5]}{' ...' if len(missing_ann) > 5 else ''}")

    # ---- 04 human factuality (recommended) --------------------------------
    fpath = base / "04_human_factuality.csv"
    if fpath.exists():
        with fpath.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            need = {"pair_id", "transform_id", "kind", "human_equivalent",
                    "annotator_id"}
            if reader.fieldnames is None or not need.issubset(reader.fieldnames):
                rep.err("04_human_factuality.csv",
                        f"missing columns; need at least {sorted(need)}")
            else:
                n = 0
                for row in reader:
                    n += 1
                    if row["kind"] not in {"benign", "altering"}:
                        rep.err("04_human_factuality.csv",
                                f"pair {row.get('pair_id')}: kind must be "
                                "benign|altering")
                    if row["human_equivalent"] not in {"0", "1"}:
                        rep.err("04_human_factuality.csv",
                                f"pair {row.get('pair_id')}: human_equivalent "
                                "must be 0 or 1")
                    if tf_ids and row.get("transform_id") not in tf_ids:
                        rep.warn("04_human_factuality.csv",
                                 f"pair {row.get('pair_id')}: transform_id not "
                                 "in 02_transformations")
                rep.note(f"04_human_factuality: {n} judgments")
    else:
        rep.warn("04_human_factuality.csv", "recommended file not present")

    # ---- 05 baseline outputs (optional) -----------------------------------
    bpath = base / "05_baseline_outputs.jsonl"
    if bpath.exists():
        bl = _read_jsonl(bpath, rep)
        for i, r in enumerate(bl, 1):
            _require(rep, "05_baseline_outputs.jsonl", r,
                     ["method", "doc_id", "condition", "score", "decision"], i)
        rep.note(f"05_baseline_outputs: {len(bl)} rows")
    else:
        rep.note("05_baseline_outputs.jsonl not present (optional)")

    # ---- split -------------------------------------------------------------
    spath = base / "split.json"
    if spath.exists():
        try:
            split = json.loads(spath.read_text(encoding="utf-8"))
            cal, test = set(split.get("calibration", [])), set(split.get("test", []))
            if cal & test:
                rep.err("split.json", f"docs in both splits: {sorted(cal & test)}")
            unknown = (cal | test) - src_doc_ids if src_doc_ids else set()
            if unknown:
                rep.warn("split.json", f"doc ids not in 01 source: {sorted(unknown)}")
            rep.note(f"split: {len(cal)} calibration, {len(test)} test docs")
        except json.JSONDecodeError as e:
            rep.err("split.json", f"invalid JSON ({e})")
    else:
        rep.warn("split.json", "not present (calibration/test split undefined)")

    # ---- report ------------------------------------------------------------
    print("=" * 68)
    print(f"Truthprint handoff validation: {base}")
    print("=" * 68)
    for m in rep.info:
        print(m)
    for m in rep.warnings:
        print(m)
    for m in rep.errors:
        print(m)
    print("-" * 68)
    print(f"errors={len(rep.errors)}  warnings={len(rep.warnings)}")
    if rep.errors:
        print("RESULT: NOT READY -- fix the errors above, then re-run.")
        return 1
    if placeholders:
        print("RESULT: STRUCTURALLY VALID, but transformations are still "
              "PLACEHOLDERS.\n        Replace them with real outputs before "
              "sending.")
        return 0
    print("RESULT: READY -- hand this folder to Claude.")
    return 0


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "handoff/samples"
    raise SystemExit(validate(folder))
