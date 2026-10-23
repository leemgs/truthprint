#!/usr/bin/env python3
"""Same-text comparison: token watermarks and Truthprint on one LLM's output.

Reviewers asked for a controlled comparison on the *same* text. Here one
instruction LLM (default Qwen2.5-0.5B-Instruct, CPU) rewords each source fact of
the committed corpus into a natural English sentence in three variants:

  * ``none``    -- unwatermarked sampling. Truthprint uses this text: the facts
                   are registered, and, as in the paper's encoder, a candidate is
                   accepted only if the Stage-2 extractor reads back the same
                   core6 record (up to ``--tries`` samples; otherwise the sentence
                   has no valid realization and counts as a failure);
  * ``kgw``     -- green-list watermark (Kirchenbauer et al.), gamma 0.25, delta 2;
  * ``synthid`` -- SynthID-Text via ``transformers`` (tournament sampling),
                   detected with the mean g-value score.

All variants are translated by the same NLLB-200-distilled-600M system. Each
document is 16 sentences; detection is per document. Token watermarks are
calibrated on the unwatermarked documents (null); Truthprint authenticates
against the registered facts and is searched without an identifier for false
attributions.

Stages cache to ``--work`` (generations.jsonl, translations.jsonl), so the run
can be resumed. Usage:
    python3 scripts/eval_same_text.py ../paper/results/realmt_b2 --docs 30 \
        --work ../paper/results/same_text --out ../paper/results/same_text
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint.multilingual import extract_invariants  # noqa: E402
from truthprint.provenance import CONTRACTS  # noqa: E402
from truthprint.stats import wilson_ci  # noqa: E402

GEN_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
MT_MODEL = "facebook/nllb-200-distilled-600M"
NLLB = {"en": "eng_Latn", "ko": "kor_Hang", "ar": "arb_Arab", "de": "deu_Latn",
        "zh": "zho_Hans", "hi": "hin_Deva"}
GAMMA, DELTA, KGW_KEY = 0.25, 2.0, 15485863
SYNTHID_KEYS = [654, 400, 836, 123, 340, 443, 597, 160, 57, 29, 590, 639, 13, 715, 468,
                990, 966, 226, 324, 585, 118, 504, 402, 641, 506, 302, 485, 441, 525, 215]
NGRAM = 5
CORE6 = CONTRACTS["core6"]
PROMPT = ("Rewrite the following as one natural English sentence. Keep every fact exactly "
          "(who, what, how many, when, negation, certainty, source of the claim, cause). "
          "Output only the sentence.\n\n{src}")


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def append_jsonl(p: Path, rows: list[dict]) -> None:
    with p.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def record(inv: dict) -> tuple:
    return tuple(inv.get(f) for f in CORE6)


# ----------------------------------------------------------------- generation
class KGWProcessor:
    """Green-list logits bias seeded by the previous token."""

    def __init__(self, vocab: int):
        import torch
        self.torch, self.vocab, self.k = torch, vocab, int(GAMMA * vocab)

    def green(self, prev: int):
        g = self.torch.Generator()
        g.manual_seed((int(prev) * KGW_KEY) % (2 ** 63))
        return self.torch.randperm(self.vocab, generator=g)[: self.k]

    def __call__(self, input_ids, scores):
        for b in range(input_ids.shape[0]):
            scores[b, self.green(input_ids[b, -1].item())] += DELTA
        return scores


def generate(sources: list[dict], work: Path, tries: int, seed: int) -> None:
    import torch
    from transformers import (AutoModelForCausalLM, AutoTokenizer, LogitsProcessorList,
                              SynthIDTextWatermarkingConfig)
    out = work / "generations.jsonl"
    done = {(r["sent_id"], r["variant"]) for r in read_jsonl(out)}
    todo = [s for s in sources if any((s["sent_id"], v) not in done for v in ("none", "kgw", "synthid"))]
    if not todo:
        return
    torch.manual_seed(seed)
    torch.set_num_threads(4)
    tok = AutoTokenizer.from_pretrained(GEN_MODEL)
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(GEN_MODEL).eval()
    vocab = model.get_output_embeddings().weight.shape[0]
    kgw = LogitsProcessorList([KGWProcessor(vocab)])
    synth = SynthIDTextWatermarkingConfig(keys=SYNTHID_KEYS, ngram_len=NGRAM)

    def run(batch: list[dict], **kw) -> list[str]:
        msgs = [[{"role": "user", "content": PROMPT.format(src=s["source_text"])}] for s in batch]
        enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt",
                                      padding=True, return_dict=True)
        with torch.no_grad():
            ids = model.generate(**enc, max_new_tokens=60, do_sample=True, top_k=0,
                                 temperature=0.7, pad_token_id=tok.eos_token_id, **kw)
        return [tok.decode(x[enc["input_ids"].shape[1]:], skip_special_tokens=True).strip().split("\n")[0]
                for x in ids]

    B = 8
    for i in range(0, len(todo), B):
        batch = todo[i:i + B]
        rows = []
        # Truthprint arm: unwatermarked candidates, accept the first whose core6 record reads back
        accepted = {s["sent_id"]: None for s in batch}
        first = {}
        for t in range(tries):
            pending = [s for s in batch if accepted[s["sent_id"]] is None]
            if not pending:
                break
            for s, text in zip(pending, run(pending)):
                first.setdefault(s["sent_id"], text)
                if record(extract_invariants(text, "en")) == record(s["gold"]):
                    accepted[s["sent_id"]] = (text, t + 1)
        for s in batch:
            a = accepted[s["sent_id"]]
            rows.append({"sent_id": s["sent_id"], "doc_id": s["doc_id"], "variant": "none",
                         "text": a[0] if a else first[s["sent_id"]], "valid": a is not None,
                         "tries": a[1] if a else tries})
        for s, text in zip(batch, run(batch, logits_processor=kgw)):
            rows.append({"sent_id": s["sent_id"], "doc_id": s["doc_id"], "variant": "kgw", "text": text})
        for s, text in zip(batch, run(batch, watermarking_config=synth)):
            rows.append({"sent_id": s["sent_id"], "doc_id": s["doc_id"], "variant": "synthid", "text": text})
        append_jsonl(out, rows)
        print(f"[generate] {min(i + B, len(todo))}/{len(todo)}", flush=True)


# ---------------------------------------------------------------- translation
def translate(work: Path, conds: list[str]) -> None:
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    gens = read_jsonl(work / "generations.jsonl")
    out = work / "translations.jsonl"
    done = {(r["sent_id"], r["variant"], r["condition"]) for r in read_jsonl(out)}
    jobs = [(g, c) for g in gens for c in conds if (g["sent_id"], g["variant"], c) not in done]
    if not jobs:
        return
    torch.set_num_threads(4)
    tok = AutoTokenizer.from_pretrained(MT_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(MT_MODEL).eval()
    tok.src_lang = NLLB["en"]
    B = 16
    for c in conds:
        cj = [g for g, cc in jobs if cc == c]
        for i in range(0, len(cj), B):
            batch = cj[i:i + B]
            enc = tok([g["text"] for g in batch], return_tensors="pt", padding=True,
                      truncation=True, max_length=128)
            with torch.no_grad():
                ids = model.generate(**enc, forced_bos_token_id=tok.convert_tokens_to_ids(NLLB[c]),
                                     max_length=160)
            texts = tok.batch_decode(ids, skip_special_tokens=True)
            append_jsonl(out, [{"sent_id": g["sent_id"], "doc_id": g["doc_id"], "variant": g["variant"],
                                "condition": c, "text": t} for g, t in zip(batch, texts)])
            print(f"[translate {c}] {min(i + B, len(cj))}/{len(cj)}", flush=True)


# -------------------------------------------------------------------- scoring
def roc_auc(pos: list[float], neg: list[float]) -> float:
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def score(sources: list[dict], work: Path, conds: list[str]) -> dict:
    import torch
    from transformers import AutoTokenizer
    from transformers.generation.logits_process import SynthIDTextWatermarkLogitsProcessor
    tok = AutoTokenizer.from_pretrained(GEN_MODEL)
    gens = read_jsonl(work / "generations.jsonl")
    trans = read_jsonl(work / "translations.jsonl")
    text = {}  # (variant, condition, sent_id) -> text
    for g in gens:
        text[(g["variant"], "clean", g["sent_id"])] = g["text"]
    for t in trans:
        text[(t["variant"], t["condition"], t["sent_id"])] = t["text"]
    valid = {g["sent_id"]: g.get("valid", False) for g in gens if g["variant"] == "none"}
    docs = defaultdict(list)
    gold = {}
    for s in sources:
        docs[s["doc_id"]].append(s["sent_id"])
        gold[s["sent_id"]] = s["gold"]
    kgw = KGWProcessor(151936)
    synth = SynthIDTextWatermarkLogitsProcessor(ngram_len=NGRAM, keys=SYNTHID_KEYS,
                                                sampling_table_size=65536, sampling_table_seed=0,
                                                context_history_size=1024, device=torch.device("cpu"))

    def ids_of(doc: str, variant: str, cond: str) -> list[int]:
        joined = " ".join(text[(variant, cond, sid)] for sid in docs[doc])
        return tok(joined, add_special_tokens=False)["input_ids"]

    def kgw_z(ids: list[int]) -> float:
        n = len(ids) - 1
        if n <= 0:
            return 0.0
        hits = sum(1 for a, b in zip(ids, ids[1:]) if (kgw.green(a) == b).any().item())
        return (hits - GAMMA * n) / math.sqrt(n * GAMMA * (1 - GAMMA))

    def synth_mean(ids: list[int]) -> float:
        x = torch.tensor([ids])
        g = synth.compute_g_values(x)                      # (1, T-NGRAM+1, depth)
        m = synth.compute_context_repetition_mask(x)       # (1, T-NGRAM+1)
        m = m[:, :g.shape[1]].unsqueeze(-1).to(g.dtype)
        denom = m.sum() * g.shape[-1]
        return float((g * m).sum() / denom) if denom > 0 else 0.5

    res = {"generator": GEN_MODEL, "translator": MT_MODEL, "docs": len(docs),
           "sentences": len(sources), "truthprint_valid_realization": wilson_ci(sum(valid.values()), len(valid)),
           "conditions": {}}
    for cond in ["clean"] + conds:
        row = {}
        for method, fn, variant in (("KGW", kgw_z, "kgw"), ("SynthID-Text", synth_mean, "synthid")):
            pos = [fn(ids_of(d, variant, cond)) for d in docs]
            neg = [fn(ids_of(d, "none", cond)) for d in docs]
            thr = max(neg)
            row[method] = {"tpr_above_max_null": wilson_ci(sum(p > thr for p in pos), len(pos)),
                           "roc_auc": round(roc_auc(pos, neg), 4),
                           "mean_pos": round(sum(pos) / len(pos), 4), "mean_null": round(sum(neg) / len(neg), 4)}
            if method == "KGW":
                row[method]["tpr_z_ge_4"] = wilson_ci(sum(p >= 4 for p in pos), len(pos))
        # Truthprint: registered facts, extraction from the translated validated text
        index = defaultdict(set)
        for d, sids in docs.items():
            for sid in sids:
                index[record(gold[sid])].add(d)
        lang = "en" if cond == "clean" else cond
        own = false_docs = sent_ok = sent_n = 0
        for d, sids in docs.items():
            hits = Counter()
            for sid in sids:
                sent_n += 1
                obs = record(extract_invariants(text[("none", cond, sid)], lang)) if valid[sid] else None
                if obs is not None and obs == record(gold[sid]):
                    sent_ok += 1
                for doc in (index.get(obs, ()) if obs is not None else ()):
                    hits[doc] += 1
            attributed = {doc for doc, c in hits.items() if c >= 0.5 * len(sids)}
            own += d in attributed
            false_docs += bool(attributed - {d})
        row["Truthprint (core6)"] = {"document_attribution": wilson_ci(own, len(docs)),
                                     "sentence_authentication": wilson_ci(sent_ok, sent_n),
                                     "docs_with_false_attribution": wilson_ci(false_docs, len(docs))}
        res["conditions"][cond] = row
    return res


def render(res: dict) -> str:
    v = res["truthprint_valid_realization"]
    L = ["# Same-text comparison: token watermarks vs Truthprint on one LLM's output", "",
         f"Generator `{res['generator']}` (CPU) rewords the source facts of {res['docs']} committed documents "
         f"({res['sentences']} sentences) in three variants (unwatermarked, KGW, SynthID-Text); translator "
         f"`{res['translator']}`. Detection per 16-sentence document. Token watermarks: TPR above the "
         "maximum unwatermarked score (empirical FPR 0 over the null documents) and ROC-AUC; Truthprint: "
         "document attribution against the registered facts (>= 50% of sentences), id-free false attributions.",
         "", f"Truthprint validated realizations (Stage-2 reads back the core6 record within the try budget): "
         f"{v[0]:.3f} [{v[1]:.3f},{v[2]:.3f}]", "",
         "| Condition | KGW TPR (> max null) | KGW AUC | SynthID TPR (> max null) | SynthID AUC | "
         "Truthprint doc attribution | Truthprint sentence auth | Truthprint docs w/ false attribution |",
         "|---|---|---|---|---|---|---|---|"]
    f = lambda t: f"{t[0]:.3f} [{t[1]:.3f},{t[2]:.3f}]"  # noqa: E731
    for cond, r in res["conditions"].items():
        k, s, t = r["KGW"], r["SynthID-Text"], r["Truthprint (core6)"]
        L.append(f"| {cond} | {f(k['tpr_above_max_null'])} | {k['roc_auc']:.3f} | {f(s['tpr_above_max_null'])} | "
                 f"{s['roc_auc']:.3f} | {f(t['document_attribution'])} | {f(t['sentence_authentication'])} | "
                 f"{f(t['docs_with_false_attribution'])} |")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="committed real-MT run with 01_source_items.jsonl")
    ap.add_argument("--docs", type=int, default=30)
    ap.add_argument("--conds", nargs="+", default=["ko", "ar", "de"])
    ap.add_argument("--tries", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20261023)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--stage", choices=["all", "generate", "translate", "score"], default="all")
    args = ap.parse_args()
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    sources = []
    for doc in read_jsonl(Path(args.folder) / "01_source_items.jsonl")[: args.docs]:
        for f in doc["facts"]:
            sources.append({"sent_id": f["sent_id"], "doc_id": doc["doc_id"],
                            "gold": {k: v for k, v in f.items() if k != "sent_id"},
                            "source_text": doc["watermarked_text"][f["sent_id"]]})
    if args.stage in ("all", "generate"):
        generate(sources, work, args.tries, args.seed)
    if args.stage in ("all", "translate"):
        translate(work, args.conds)
    if args.stage in ("all", "score"):
        res = score(sources, work, args.conds)
        md = render(res)
        if args.out:
            Path(args.out + ".json").write_text(json.dumps(res, indent=2), encoding="utf-8")
            Path(args.out + ".md").write_text(md, encoding="utf-8")
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
