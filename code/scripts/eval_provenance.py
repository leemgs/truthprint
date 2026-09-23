#!/usr/bin/env python3
"""Measure meaning-based provenance authentication on real MT output.

End-to-end, on the real NLLB translations in a handoff folder:
  * TPR: a translated sentence authenticates against its own registered tag
    (the Stage-2 extractor recovers the contract fields) -- per language and
    per invariant contract, with Wilson 95% CIs;
  * document-level attribution (>= 50% of sentences authenticate);
  * tamper rejection: a meaning-altering edit to a contract field must fail;
  * false positives: authenticate against tags from other sentences (should be
    ~0; cryptographic bound 2^-tau).

This is the translation-robust, meaning-layer counterpart to the surface-carrier
pilot (which scored 0/192): provenance is verified as consistency with a
participating keyed generator, not via a hidden surface payload.

Usage: python3 scripts/eval_provenance.py /path/to/handoff_folder [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint.multilingual import extract_invariants, FIELDS
from truthprint.provenance import (CONTRACTS, register_tag, authenticate,
                                   document_attribution)
from truthprint.stats import wilson_ci

REFERENCE_KEY = b"truthprint-challenge-key-01234567"[:32]
_LANG = {"ko": "ko", "hi": "hi", "zh": "zh", "ar": "ar", "de": "de", "rt": "en"}
TAG_BITS = 32


def _read_jsonl(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _tamper(inv: dict, fields: list[str], rng: random.Random) -> dict:
    """Flip one contract field to a different value (meaning-altering edit)."""
    alts = {
        "polarity": ["positive", "negative"],
        "time_dir": ["previous", "following"],
        "modality": ["asserted", "necessary", "possible"],
        "attribution": ["none", "report", "vendor"],
        "predicate": ["FIX", "BREAK"],
        "agent": ["the developer", "the engineer", "the operator", "the analyst"],
        "quantity": [1, 2, 3, 5, 8],
        "patient": ["server error", "memory leak", "config drift", "cache miss"],
        "causation": ["none", "cause", "purpose"],
    }
    f = rng.choice([x for x in fields if x in alts])
    cur = inv.get(f)
    choices = [v for v in alts[f] if v != cur] or alts[f]
    out = dict(inv)
    out[f] = rng.choice(choices)
    return out


def evaluate(folder: str, key: bytes = REFERENCE_KEY, nonce: bytes = b"prov-nonce-01") -> dict:
    base = Path(folder)
    src = {}
    docs = defaultdict(list)  # doc_id -> [sent_id...]
    for r in _read_jsonl(base / "01_source_items.jsonl"):
        for f in r["facts"]:
            src[f["sent_id"]] = {k: f[k] for k in FIELDS}
            docs[r["doc_id"]].append(f["sent_id"])
    tf = _read_jsonl(base / "02_transformations.jsonl")
    if not tf:
        return {"error": "02_transformations.jsonl is empty."}
    rng = random.Random(7)

    out = {"tag_bits": TAG_BITS, "contracts": {}}
    for cname in CONTRACTS:
        conds = {}
        # per condition: TPR, tamper-rejection, doc-attribution, FP
        per = defaultdict(lambda: {"tp": 0, "n": 0, "tamper_rej": 0, "tamper_n": 0,
                                   "fp": 0, "fp_n": 0,
                                   "doc_ok": 0, "doc_n": 0,
                                   "doc_flags": defaultdict(list)})
        # collect registered tags for FP test
        reg = {}
        for sid, gold in src.items():
            reg[sid] = register_tag(key, gold, nonce, sid, cname, TAG_BITS)
        for t in tf:
            tag = t["transform_id"].rsplit("-", 1)[1]
            lang = _LANG.get(tag)
            if lang is None or t["sent_id"] not in src:
                continue
            sid = t["sent_id"]
            obs = extract_invariants(t["output_text"], lang)
            p = per[tag]
            # TPR: authenticate against own registered tag
            ok = authenticate(key, obs, nonce, sid, reg[sid], cname, TAG_BITS)
            p["tp"] += 1 if ok else 0
            p["n"] += 1
            p["doc_flags"][t["doc_id"]].append(ok)
            # tamper: register tag on a meaning-altered gold; observed must NOT match
            tampered = _tamper(src[sid], CONTRACTS[cname], rng)
            ttag = register_tag(key, tampered, nonce, sid, cname, TAG_BITS)
            t_ok = authenticate(key, obs, nonce, sid, ttag, cname, TAG_BITS)
            p["tamper_rej"] += 0 if t_ok else 1
            p["tamper_n"] += 1
            # FP: authenticate observed against a different sentence's tag
            other = rng.choice([s for s in src if s != sid])
            f_ok = authenticate(key, obs, nonce, other, reg[other], cname, TAG_BITS)
            p["fp"] += 1 if f_ok else 0
            p["fp_n"] += 1
        for tag, p in per.items():
            doc_ok = sum(1 for d, flags in p["doc_flags"].items()
                         if document_attribution(flags, 0.5))
            conds[tag] = {
                "lang": _LANG[tag],
                "sentence_tpr": wilson_ci(p["tp"], p["n"]),
                "tamper_rejection": wilson_ci(p["tamper_rej"], p["tamper_n"]),
                "document_attribution": wilson_ci(doc_ok, len(p["doc_flags"])),
                "false_positive": wilson_ci(p["fp"], p["fp_n"]),
                "n_sent": p["n"], "n_doc": len(p["doc_flags"]),
            }
        out["contracts"][cname] = {"fields": CONTRACTS[cname], "conditions": conds}
    return out


def _fmt(res: dict) -> str:
    if "error" in res:
        return f"# Provenance authentication\n\n**{res['error']}**\n"
    L = ["# Meaning-based provenance authentication on real MT output", "",
         f"Verifier re-extracts invariants (Stage-2) and checks a keyed "
         f"{res['tag_bits']}-bit tag over an invariant contract; the tag lives "
         "in an out-of-band ledger, not the text. Contrast: the surface-carrier "
         "pilot scored 0/192. FPR bound per test = 2^-tau.", ""]
    for cname, c in res["contracts"].items():
        L.append(f"## Contract `{cname}` = {c['fields']}")
        L.append("")
        L.append("| Condition | Sentence TPR (95% CI) | Document attribution | "
                 "Tamper rejection | False positive |")
        L.append("|---|---|---|---|---|")
        for tag, d in sorted(c["conditions"].items()):
            def ci(x):
                return f"{x[0]:.3f} [{x[1]:.3f},{x[2]:.3f}]"
            L.append(f"| {tag} ({d['lang']}) | {ci(d['sentence_tpr'])} | "
                     f"{ci(d['document_attribution'])} | "
                     f"{ci(d['tamper_rejection'])} | {ci(d['false_positive'])} |")
        L.append("")
    L += ["> Meaning-based authentication survives real translation where the "
          "surface carrier does not; a wider contract authenticates more meaning "
          "but is more sensitive to extraction noise (fidelity/robustness "
          "trade-off). Closed-domain Stage-2; wide-coverage parsing is future work.",
          ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    res = evaluate(args.folder)
    md = _fmt(res)
    print(md)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        Path(args.out).with_suffix(".json").write_text(json.dumps(res, indent=2),
                                                       encoding="utf-8")
        print(f"[written] {args.out}")
    return 0 if "error" not in res else 1


if __name__ == "__main__":
    raise SystemExit(main())
