#!/usr/bin/env python3
"""Build and translate an edited-text tamper corpus (CPU, NLLB).

For every source sentence of the committed real-MT run (``realmt_b2``) one field
of its fact is changed and the *edited text* is re-realized with the same
template choice (``realize(f, 0, 0)``), then translated by the same NLLB system
as the main run (five direct translations and a Korean round trip). The ledger
keeps the *original* registration, so a verifier that accepts a translated
edited sentence is a false accept.

Edited fields cycle over the sentences: five in the core6 contract (polarity,
quantity, time_dir, attribution, agent; the predicate has a single realizable
value) and three outside it (modality, causation, patient), which core6 should
accept by design and full9 should reject. 100 sentences per field.

Usage: python3 scripts/make_edited_tamper.py ../paper/results/realmt_b2 \
           ../paper/results/edited_tamper [--cache DIR]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from truthprint import challenge as ch  # noqa: E402
from make_realmt import translate  # noqa: E402

SEED = 20261108
EDIT_FIELDS = ["polarity", "quantity", "time_dir", "attribution", "agent",
               "modality", "causation", "patient"]


def _fact(d: dict) -> ch.ExtFact:
    return ch.ExtFact(agent=d["agent"], patient=d["patient"], quantity=d["quantity"],
                      polarity=d["polarity"], time_dir=d["time_dir"], modality=d["modality"],
                      attribution=d["attribution"], causation=d["causation"])


def edit(f: ch.ExtFact, field: str, rng: random.Random) -> ch.ExtFact:
    if field == "agent":
        return replace(f, agent=rng.choice([a for a in ch.AGENTS if a != f.agent]))
    if field == "patient":
        return replace(f, patient=rng.choice([p for p in ch.PATIENTS if p != f.patient]))
    return ch.altering_edit(f, field, rng)


def build(src_folder: Path) -> list[dict]:
    rng = random.Random(SEED)
    rows, i = [], 0
    for line in (src_folder / "01_source_items.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        text, facts, edits = {}, [], {}
        for d in r["facts"]:
            sid = d["sent_id"]
            f = _fact(d)
            assert ch.realize(f, 0, 0) == r["watermarked_text"][sid]  # same template choice
            field = EDIT_FIELDS[i % len(EDIT_FIELDS)]
            g = edit(f, field, rng)
            text[sid] = ch.realize(g, 0, 0)
            facts.append(dict(ch.ext_invariants(g), sent_id=sid))
            edits[sid] = field
            i += 1
        rows.append({"doc_id": r["doc_id"], "lang_src": "en", "facts": facts,
                     "edited_field": edits, "watermarked_text": text})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("out")
    ap.add_argument("--cache", default=None, help="checkpoint folder for resumable runs")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = build(Path(args.source))
    with (out / "01_edited_items.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    cache = Path(args.cache) if args.cache else None
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
    tf = translate(rows, cache)
    with (out / "02_transformations.jsonl").open("w", encoding="utf-8") as fh:
        for x in tf:
            fh.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(f"wrote {len(tf)} translations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
