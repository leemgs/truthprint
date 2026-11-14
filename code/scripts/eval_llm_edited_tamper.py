#!/usr/bin/env python3
"""Tamper test with free LLM wording: an edited fact, reworded by an LLM, then translated.

The template-edited sentences of ``edited_tamper/01_edited_items.jsonl`` (one
field changed per sentence) are reworded by the same generator and prompt as
the same-text run (Qwen2.5-0.5B-Instruct, one unwatermarked sample, temperature
0.7), so the edited text is no longer template wording. The rewording is then
translated by NLLB-200-distilled-600M into ko/ar/de, and every version (clean
English and translations) is verified against the tag registered for the
*original, unedited* source. Per contract and edited field:

* ``accepted``   - authenticates against the original record (a false accept for
                   an edit to a contract field);
* ``reads_edit`` - the re-extracted record equals the edited one.

All 50 documents (800 sentences) are used, matching the same-text run.
Stages cache to ``--work`` (``generations.jsonl``, ``translations.jsonl``).

Usage: python3 scripts/eval_llm_edited_tamper.py ../paper/results/realmt_b2 \
           ../paper/results/edited_tamper --work ../paper/results/llm_edited_tamper \
           [--stage all|generate|translate|score] --out ../paper/results/llm_edited_tamper_eval
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_provenance import REFERENCE_KEY, TAG_BITS  # noqa: E402
from eval_same_text import GEN_MODEL, MT_MODEL, NLLB, PROMPT, append_jsonl, read_jsonl  # noqa: E402
from truthprint.multilingual import extract_invariants  # noqa: E402
from truthprint.provenance import CONTRACTS, authenticate, register_tag  # noqa: E402
from truthprint.stats import wilson_ci  # noqa: E402

NONCE = b"prov-nonce-01"
SEED = 20261110
DOCS = 50
CONDS = ["ko", "ar", "de"]


def sources(edited: Path) -> list[dict]:
    out = []
    for r in read_jsonl(edited / "01_edited_items.jsonl")[:DOCS]:
        for f in r["facts"]:
            sid = f["sent_id"]
            out.append({"sent_id": sid, "doc_id": r["doc_id"], "field": r["edited_field"][sid],
                        "edited": {k: v for k, v in f.items() if k != "sent_id"},
                        "text": r["watermarked_text"][sid]})
    return out


def generate(src: list[dict], work: Path) -> None:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    out = work / "generations.jsonl"
    done = {r["sent_id"] for r in read_jsonl(out)}
    torch.set_num_threads(4)
    tok = AutoTokenizer.from_pretrained(GEN_MODEL)
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(GEN_MODEL).eval()
    B = 8
    for i in range(0, len(src), B):
        batch = src[i:i + B]
        if all(s["sent_id"] in done for s in batch):
            continue
        torch.manual_seed(SEED + i)  # per-batch seed: a resumed run matches an uninterrupted one
        msgs = [[{"role": "user", "content": PROMPT.format(src=s["text"])}] for s in batch]
        enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt",
                                      padding=True, return_dict=True)
        with torch.no_grad():
            ids = model.generate(**enc, max_new_tokens=60, do_sample=True, top_k=0, temperature=0.7,
                                 pad_token_id=tok.eos_token_id)
        texts = [tok.decode(x[enc["input_ids"].shape[1]:], skip_special_tokens=True).strip().split("\n")[0]
                 for x in ids]
        append_jsonl(out, [{"sent_id": s["sent_id"], "doc_id": s["doc_id"], "text": t}
                           for s, t in zip(batch, texts)])
        print(f"[generate] {min(i + B, len(src))}/{len(src)}", flush=True)


def translate(work: Path) -> None:
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    gens = read_jsonl(work / "generations.jsonl")
    out = work / "translations.jsonl"
    done = {(r["sent_id"], r["condition"]) for r in read_jsonl(out)}
    torch.set_num_threads(4)
    tok = AutoTokenizer.from_pretrained(MT_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(MT_MODEL).eval()
    tok.src_lang = NLLB["en"]
    B = 16
    for c in CONDS:
        for i in range(0, len(gens), B):
            batch = gens[i:i + B]
            if all((g["sent_id"], c) in done for g in batch):
                continue
            enc = tok([g["text"] for g in batch], return_tensors="pt", padding=True,
                      truncation=True, max_length=128)
            with torch.no_grad():
                ids = model.generate(**enc, forced_bos_token_id=tok.convert_tokens_to_ids(NLLB[c]),
                                     max_length=160)
            append_jsonl(out, [{"sent_id": g["sent_id"], "condition": c, "text": t}
                               for g, t in zip(batch, tok.batch_decode(ids, skip_special_tokens=True))])
            print(f"[translate {c}] {min(i + B, len(gens))}/{len(gens)}", flush=True)


def score(source: Path, src: list[dict], work: Path) -> dict:
    orig = {}
    for r in read_jsonl(source / "01_source_items.jsonl"):
        for f in r["facts"]:
            orig[f["sent_id"]] = {k: v for k, v in f.items() if k != "sent_id"}
    meta = {s["sent_id"]: s for s in src}
    texts = {("clean", g["sent_id"]): g["text"] for g in read_jsonl(work / "generations.jsonl")}
    for t in read_jsonl(work / "translations.jsonl"):
        texts[(t["condition"], t["sent_id"])] = t["text"]
    out = {"generator": GEN_MODEL, "translator": MT_MODEL, "sentences": len(src),
           "conditions": ["clean"] + CONDS, "contracts": {}}
    for c in ("core6", "full9"):
        reg = {sid: register_tag(REFERENCE_KEY, orig[sid], NONCE, sid, c, TAG_BITS) for sid in meta}
        acc = defaultdict(lambda: [0, 0, 0])            # (cond, in_contract) -> [accepted, reads, n]
        per_field = defaultdict(lambda: [0, 0, 0])      # field -> [accepted, reads, n] over translations
        for (cond, sid), text in sorted(texts.items()):
            obs = extract_invariants(text, "en" if cond == "clean" else cond)
            ok = authenticate(REFERENCE_KEY, obs, NONCE, sid, reg[sid], c, TAG_BITS)
            reads = all(obs.get(k) == meta[sid]["edited"].get(k) for k in CONTRACTS[c])
            inside = meta[sid]["field"] in CONTRACTS[c]
            row = acc[(cond, inside)]
            row[0] += ok
            row[1] += reads
            row[2] += 1
            if cond != "clean":
                pf = per_field[meta[sid]["field"]]
                pf[0] += ok
                pf[1] += reads
                pf[2] += 1

        def block(inside: bool) -> dict:
            res = {}
            for cond in out["conditions"]:
                a, r_, n = acc[(cond, inside)]
                if n:
                    res[cond] = {"accepted": wilson_ci(a, n), "reads_edit": wilson_ci(r_, n), "n": n}
            tr = [acc[(k, inside)] for k in CONDS]
            a, r_, n = (sum(x[i] for x in tr) for i in range(3))
            if n:
                res["translated"] = {"accepted": wilson_ci(a, n), "reads_edit": wilson_ci(r_, n), "n": n}
            return res
        out["contracts"][c] = {
            "in_contract": block(True), "outside_contract": block(False),
            "per_field_translated": {f: {"in_contract": f in CONTRACTS[c], "n": v[2],
                                         "accepted": wilson_ci(v[0], v[2]),
                                         "reads_edit": wilson_ci(v[1], v[2])}
                                     for f, v in sorted(per_field.items())}}
    return out


def render(r: dict) -> str:
    f = lambda t: f"{t[0]:.3f} [{t[1]:.3f},{t[2]:.3f}]"  # noqa: E731
    L = ["# Tamper test with free LLM wording (edited fact, reworded, translated)", "",
         f"{r['sentences']} sentences ({r['sentences'] // 16} documents), each with one field edited, reworded once by "
         f"`{r['generator']}` (same prompt as the same-text run, no resampling), translated by "
         f"`{r['translator']}` into ko/ar/de. Verified against the tag of the *original* source "
         "(id-addressed). `accepted` on an in-contract edit is a false accept; `reads edit` = the "
         "re-extracted record equals the edited one. Wilson 95% CI.", ""]
    for c, d in r["contracts"].items():
        L += [f"## Contract `{c}`", "", "| Edit | Condition | n | Accepted | Reads edit |",
              "|---|---|---|---|---|"]
        for side, name in (("in_contract", "in contract"), ("outside_contract", "outside contract")):
            for cond, x in d[side].items():
                L.append(f"| {name} | {cond} | {x['n']} | {f(x['accepted'])} | {f(x['reads_edit'])} |")
        L += ["", "Per edited field, translated conditions pooled:", "",
              "| Field | In contract | n | Accepted | Reads edit |", "|---|---|---|---|---|"]
        for fld, x in d["per_field_translated"].items():
            L.append(f"| {fld} | {'yes' if x['in_contract'] else 'no'} | {x['n']} | "
                     f"{f(x['accepted'])} | {f(x['reads_edit'])} |")
        L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("edited")
    ap.add_argument("--work", required=True)
    ap.add_argument("--stage", choices=["all", "generate", "translate", "score"], default="all")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    src = sources(Path(args.edited))
    if args.stage in ("all", "generate"):
        generate(src, work)
    if args.stage in ("all", "translate"):
        translate(work)
    if args.stage in ("all", "score"):
        r = score(Path(args.source), src, work)
        md = render(r)
        if args.out:
            Path(args.out + ".json").write_text(json.dumps(r, indent=2), encoding="utf-8")
            Path(args.out + ".md").write_text(md, encoding="utf-8")
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
