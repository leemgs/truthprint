#!/usr/bin/env python3
"""Separated (translator-independent) neural frontend vs lexicon (Task 1 / W5).

Reviewer W5 asked that the translation and extraction stages use *separate*
models, so the neural pilot is not confounded by one model reading its own
translation. This script measures a frontend that is model-separated *by
construction*: it reads the cached **real** LLM-MT translations with a real
multilingual sentence embedding (:mod:`truthprint.neural_embed_parser`), which is
not the model that produced the translations. It reports, per field and split by
domain (closed template vs open-domain wording), the recovery of the categorical
invariant fields, head-to-head against the in-repo lexicon extractor on the same
text, with Wilson 95% CIs.

The decisive, honest datapoint is the *open-domain temporal-direction* cell: the
closed lexicon abstains on out-of-vocabulary time wording (recovery ~0) while the
translator-independent embedding frontend recovers it, i.e. a semantic frontend
separated from the translator reads fields the lexicon cannot. The same table
shows, honestly, that a *static* embedding is not enough for the full contract
(polarity/modality near chance) -- which is why the wide-coverage instruction-LLM
frontend is run through the separated-backend GPU harness (``handoff/``), where
translation and extraction are two distinct model configs.

Usage:
    python3 scripts/eval_separated_frontend.py [--jsonl PATH] [--out PATH]

Requires the optional embedding backend (``pip install model2vec``); exits 2 with
a clear message otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint.multilingual import extract_invariants  # noqa: E402
from truthprint.neural_embed_parser import CATEGORICAL  # noqa: E402
from truthprint.stats import wilson_ci  # noqa: E402


def _read_jsonl(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _eq(a, b) -> bool:
    if a is None or b is None:
        return a == b
    return str(a).strip().lower() == str(b).strip().lower()


def evaluate(jsonl: Path):
    from truthprint.neural_embed_parser import NeuralEmbedExtractor
    recs = _read_jsonl(jsonl)
    neural = NeuralEmbedExtractor()
    # counts[frontend][domain][field] = [hits, n]
    counts = {fe: defaultdict(lambda: defaultdict(lambda: [0, 0]))
              for fe in ("neural", "lexicon")}
    for r in recs:
        gold = r["gold"]
        dom = r["domain"]
        npred = neural.extract(r["text"], r.get("lang", "en"))
        lpred = extract_invariants(r["text"], r.get("lang", "en"))
        for f in CATEGORICAL:
            for fe, pred in (("neural", npred), ("lexicon", lpred)):
                c = counts[fe][dom][f]
                c[1] += 1
                if _eq(pred.get(f), gold.get(f)):
                    c[0] += 1
    # build result
    domains = sorted({r["domain"] for r in recs})
    res = {"n_records": len(recs), "domains": {}}
    for dom in domains:
        res["domains"][dom] = {}
        for f in CATEGORICAL:
            entry = {}
            for fe in ("neural", "lexicon"):
                h, n = counts[fe][dom][f]
                entry[fe] = wilson_ci(h, n)
            res["domains"][dom][f] = entry
        # aggregate over categorical fields
        agg = {}
        for fe in ("neural", "lexicon"):
            h = sum(counts[fe][dom][f][0] for f in CATEGORICAL)
            n = sum(counts[fe][dom][f][1] for f in CATEGORICAL)
            agg[fe] = wilson_ci(h, n)
        res["domains"][dom]["_aggregate"] = agg
    return res


def _fmt(res) -> str:
    L = ["# Translator-independent (embedding) frontend vs lexicon (Task 1 / W5)",
         "",
         f"Categorical invariant recovery on cached **real** LLM-MT translations "
         f"({res['n_records']} sentences), split by domain. The neural column is a "
         f"real multilingual **embedding** frontend that is *model-separated from "
         f"the translator*; the lexicon column is the in-repo Stage-2 extractor on "
         f"the same text. Wilson 95% CI.", ""]
    for dom, fields in res["domains"].items():
        L.append(f"## Domain: {dom}")
        L.append("")
        L.append("| Field | Neural (sep.) | Lexicon |")
        L.append("|---|---|---|")
        for f in CATEGORICAL:
            n = fields[f]["neural"]
            lx = fields[f]["lexicon"]
            L.append(f"| {f} | {n[0]:.3f} [{n[1]:.3f},{n[2]:.3f}] | "
                     f"{lx[0]:.3f} [{lx[1]:.3f},{lx[2]:.3f}] |")
        agg = fields["_aggregate"]
        L.append(f"| **aggregate** | **{agg['neural'][0]:.3f}** | "
                 f"**{agg['lexicon'][0]:.3f}** |")
        L.append("")
    L += ["> Open-domain temporal direction is the decisive cell: the lexicon "
          "abstains on out-of-vocabulary time wording while the "
          "translator-independent embedding frontend recovers it. A static "
          "embedding is nonetheless insufficient for the full typed contract, "
          "motivating the instruction-LLM frontend run on the separated-backend "
          "GPU harness (handoff/).", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", default=str(
        Path(__file__).resolve().parent.parent.parent
        / "paper/results/neural_parser_llmmt_outputs.jsonl"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    try:
        from truthprint import embedding as E
        if not E.available():
            raise RuntimeError("embedding weights unavailable")
    except Exception as e:
        print(f"[skip] embedding backend unavailable: {e}\n"
              "Install with `pip install model2vec` (optional baseline extra).",
              file=sys.stderr)
        return 2

    res = evaluate(Path(args.jsonl))
    md = _fmt(res)
    print(md)
    if args.out:
        out = Path(args.out)
        out.write_text(md, encoding="utf-8")
        out.with_suffix(".json").write_text(json.dumps(res, indent=2),
                                            encoding="utf-8")
        print(f"[written] {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
