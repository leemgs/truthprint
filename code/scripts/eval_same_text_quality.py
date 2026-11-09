#!/usr/bin/env python3
"""Fluency proxy for the same-text generations: perplexity under a separate LM.

Scores every clean English sentence of ``same_text/generations.jsonl`` with
GPT-2 (a different model from the Qwen2.5-0.5B generator, so it does not favor
the generator's own distribution). Reported per variant: the geometric-mean
perplexity over sentences with a 95% CI (normal approximation on per-sentence
log-perplexity), and the paired difference to the unwatermarked first sample.

This is an automatic proxy for objective (ii), not a human quality judgment:
perplexity rewards predictable wording and says nothing about factual accuracy.

Usage: python3 scripts/eval_same_text_quality.py ../paper/results/same_text \
           --out ../paper/results/same_text_quality
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

LM = "openai-community/gpt2"


def _jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _ci(xs: list[float]) -> list[float]:
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    h = 1.96 * sd / math.sqrt(n)
    return [m, m - h, m + h]


def evaluate(work: Path) -> dict:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(4)
    tok = AutoTokenizer.from_pretrained(LM)
    model = AutoModelForCausalLM.from_pretrained(LM).eval()

    def logppl(text: str) -> float:
        ids = tok(tok.bos_token + text, return_tensors="pt")["input_ids"]
        with torch.no_grad():
            loss = model(ids, labels=ids).loss
        return float(loss)

    gens = _jsonl(work / "generations.jsonl")
    texts = {}
    for g in gens:
        texts.setdefault(g["sent_id"], {})[g["variant"]] = g["text"]
        if g["variant"] == "none" and "first_text" in g:
            texts[g["sent_id"]]["first"] = g["first_text"]
    variants = {"first": "Unwatermarked, first sample", "kgw": "KGW", "synthid": "SynthID-Text",
                "none": "Truthprint (validated)"}
    sids = sorted(s for s in texts if all(v in texts[s] for v in variants))
    lp = {v: [logppl(texts[s][v]) for s in sids] for v in variants}
    out = {"lm": LM, "sentences": len(sids), "variants": {}}
    for v, name in variants.items():
        m = _ci(lp[v])
        d = _ci([a - b for a, b in zip(lp[v], lp["first"])])
        out["variants"][v] = {"name": name, "ppl_geomean": [math.exp(x) for x in m],
                              "log_ppl_diff_vs_first": d}
    return out


def render(r: dict) -> str:
    L = ["# Same-text fluency proxy (perplexity under GPT-2)", "",
         f"{r['sentences']} clean English sentences per variant, scored by `{r['lm']}` (not the "
         "generator). Geometric-mean perplexity with a 95% CI, and the paired mean difference in "
         "log-perplexity to the unwatermarked first sample (> 0 means less predictable wording). "
         "An automatic proxy, not a human quality judgment.", "",
         "| Variant | Perplexity (95% CI) | Δ log-PPL vs. first sample (95% CI) |", "|---|---|---|"]
    for v in r["variants"].values():
        p, d = v["ppl_geomean"], v["log_ppl_diff_vs_first"]
        L.append(f"| {v['name']} | {p[0]:.1f} [{p[1]:.1f},{p[2]:.1f}] | "
                 f"{d[0]:+.3f} [{d[1]:+.3f},{d[2]:+.3f}] |")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    r = evaluate(Path(args.work))
    md = render(r)
    if args.out:
        Path(args.out + ".json").write_text(json.dumps(r, indent=2), encoding="utf-8")
        Path(args.out + ".md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
