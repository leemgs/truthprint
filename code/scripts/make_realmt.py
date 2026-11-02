#!/usr/bin/env python3
"""Rebuild the real-MT corpus (``paper/results/realmt_b2``) on CPU.

Replicates cells 4 and 6 of ``handoff/Truthprint_B2_Multilingual_Kaggle.ipynb``:
the same generator seed (50 documents x 16 sentences), the same NLLB-200-
distilled-600M system, the same batch size (32), truncation and ``max_length``
(256), five direct translations and a Korean round trip. It is re-run because
the generator's plural was fixed ("cache misss" -> "cache misses").

With ``--compare OLD_FOLDER`` it reports how many translations of source
sentences that the fix did not change are identical to the old run (a check that
the CPU rebuild reproduces the original GPU run).

Usage: python3 scripts/make_realmt.py ../paper/results/realmt_b2 \
           [--compare ../paper/results/realmt_b2_legacy]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint import challenge as ch  # noqa: E402

SEED, N_DOCS, SENTS = 20260924, 50, 16
MODEL = "facebook/nllb-200-distilled-600M"
SYSTEM = f"HuggingFace/{MODEL}"
TGT = ["ko", "hi", "zh", "ar", "de"]
NLLB = {"en": "eng_Latn", "ko": "kor_Hang", "hi": "hin_Deva", "zh": "zho_Hans",
        "ar": "arb_Arab", "de": "deu_Latn"}
BATCH = 32


def sources() -> list[dict]:
    rng = random.Random(SEED)
    rows = []
    for d in range(N_DOCS):
        doc = f"D{d + 1:04d}"
        facts = [ch.sample_fact(rng) for _ in range(SENTS)]
        wm, fr = {}, []
        for i, f in enumerate(facts):
            sid = f"{doc}-s{i + 1}"
            wm[sid] = ch.realize(f, 0, 0)
            fr.append(dict(ch.ext_invariants(f), sent_id=sid))
        rows.append({"doc_id": doc, "lang_src": "en", "facts": fr, "watermarked_text": wm})
    return rows


def translate(rows: list[dict]) -> list[dict]:
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    torch.set_num_threads(4)
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL).eval()

    def tr_batch(texts, s, g):
        tok.src_lang = NLLB[s]
        bos = tok.convert_tokens_to_ids(NLLB[g])
        out = []
        for i in range(0, len(texts), BATCH):
            enc = tok(texts[i:i + BATCH], return_tensors="pt", padding=True, truncation=True,
                      max_length=256)
            with torch.no_grad():
                o = model.generate(**enc, forced_bos_token_id=bos, max_length=256)
            out.extend(tok.batch_decode(o, skip_special_tokens=True))
            print(f"  {s}->{g} {min(i + BATCH, len(texts))}/{len(texts)}", flush=True)
        return out

    items = [(r["doc_id"], sid, t) for r in rows for sid, t in r["watermarked_text"].items()]
    srcs = [t for _, _, t in items]
    tf = []
    for lg in TGT:
        for (doc, sid, _), o in zip(items, tr_batch(srcs, "en", lg)):
            tf.append({"transform_id": f"{sid}-{lg}", "doc_id": doc, "sent_id": sid,
                       "transform_type": "translation", "direction": f"en->{lg}",
                       "system": SYSTEM, "params": {}, "output_text": o, "round_trip": False})
    back = tr_batch(tr_batch(srcs, "en", "ko"), "ko", "en")
    for (doc, sid, _), o in zip(items, back):
        tf.append({"transform_id": f"{sid}-rt", "doc_id": doc, "sent_id": sid,
                   "transform_type": "roundtrip_translation", "direction": "en->ko->en",
                   "system": SYSTEM, "params": {}, "output_text": o, "round_trip": True})
    return tf


def compare(new: Path, old: Path) -> dict:
    def load(p):
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    src_new = {sid: t for r in load(new / "01_source_items.jsonl") for sid, t in r["watermarked_text"].items()}
    src_old = {sid: t for r in load(old / "01_source_items.jsonl") for sid, t in r["watermarked_text"].items()}
    changed = {sid for sid in src_new if src_new[sid] != src_old[sid]}
    tr_old = {t["transform_id"]: t["output_text"] for t in load(old / "02_transformations.jsonl")}
    same = n = 0
    for t in load(new / "02_transformations.jsonl"):
        if t["sent_id"] in changed:
            continue
        n += 1
        same += t["output_text"] == tr_old[t["transform_id"]]
    return {"changed_sources": len(changed), "unchanged_translations": n, "identical_to_old_run": same}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--compare", default=None)
    ap.add_argument("--compare-only", action="store_true")
    args = ap.parse_args()
    out = Path(args.folder)
    if not args.compare_only:
        out.mkdir(parents=True, exist_ok=True)
        rows = sources()
        with (out / "01_source_items.jsonl").open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        tf = translate(rows)
        with (out / "02_transformations.jsonl").open("w", encoding="utf-8") as fh:
            for x in tf:
                fh.write(json.dumps(x, ensure_ascii=False) + "\n")
        print(f"wrote {len(tf)} translations", flush=True)
    if args.compare:
        r = compare(out, Path(args.compare))
        (out / "rebuild_check.json").write_text(json.dumps(r, indent=2), encoding="utf-8")
        print(json.dumps(r), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
