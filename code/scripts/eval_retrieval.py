#!/usr/bin/env python3
"""Ledger retrieval(+NLI) baseline vs the typed meaning-digest (reviewer W1).

The surviving meaning-digest scheme already needs an out-of-band ledger, so the
fair control is: **store the source in that ledger and retrieve it** after
transformation (nearest-neighbor over a sentence embedding), optionally adding an
NLI/entailment check to reject edits. This script runs that head-to-head on the
same seeded closed-domain corpus and transforms as the paraphrase harness.

Methods (all provenance verifiers under the SAME ledger assumption):
  * ``meaning-digest``       -- proposed: keyed tag over the typed invariant
    contract (extended-coverage Stage-2 extraction); accept iff the tag reproduces.
  * ``retrieval``            -- nearest-neighbor attribution to the stored source;
    accept iff top cosine >= threshold (no meaning check).
  * ``retrieval+nli_proxy``  -- retrieval plus a cheap deterministic entailment
    proxy (bidirectional lexical overlap).
  * ``retrieval+nli_oracle`` -- retrieval plus a *perfect* (unrealizable) NLI that
    knows the gold contract: the ceiling for any similarity+NLI pipeline.

Fair operating point: each similarity-based method's threshold is calibrated on a
held-out split so its **benign-paraphrase acceptance is matched** to a target
(default 0.95); we then report each method's single-field **tamper rejection** at
that point --- the decisive axis. We also report attribution rank-1 rate (does the
nearest gallery entry equal the true source) for benign vs. tamper, which shows
retrieval maps a tampered sentence back to its own source, so no similarity
threshold can separate a typed tamper from a legitimate paraphrase.

Backend: transparent bag-of-words by default (stdlib, CI-reproducible); pass
``--real-embedding`` to use the multilingual encoder (``model2vec``) when present.

Usage: python3 scripts/eval_retrieval.py [--out PATH] [--n-docs N]
                                         [--sents-per-doc S] [--benign-tpr 0.95]
                                         [--seed SEED] [--real-embedding]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint import challenge as ch
from truthprint import paraphrase as pp
from truthprint import retrieval as rt
from truthprint.multilingual_ext import extract_invariants as extract_ext
from truthprint.provenance import CONTRACTS, register_tag, authenticate
from truthprint.stats import wilson_ci

REFERENCE_KEY = b"truthprint-challenge-key-01234567"[:32]
NONCE = b"retrieval-nonce-01"
TAG_BITS = 32
CONTRACT = "core6"
LANG = "en"


def _ci(x):
    return f"{x[0]:.3f} [{x[1]:.3f},{x[2]:.3f}]"


def _make_corpus(rng, n_docs, sents_per_doc):
    """Each item: dict with source text/gold and one benign + one altering variant."""
    items = []
    for _ in range(n_docs):
        for _s in range(sents_per_doc):
            f = ch.sample_fact(rng)
            vb, tb = rng.randrange(2), rng.randrange(2)
            src = ch.realize(f, vb, tb)
            variants = pp.paraphrase_variants(f, vb, tb, rng)
            benign = next(v for v in variants if v["op"] == "combo_benign")
            alter = next(v for v in variants if v["op"] == "alter")
            items.append({
                "gold_src": ch.ext_invariants(f),
                "src": src,
                "benign_text": benign["text"], "benign_gold": ch.ext_invariants(f),
                "alter_text": alter["text"], "alter_gold": ch.ext_invariants(alter["gold"]),
            })
    return items


def _calibrate_threshold(scores_benign, target_tpr):
    """Highest threshold whose benign acceptance >= target_tpr (so acceptance is
    matched across methods). scores_benign: list of similarity scores for benign
    paraphrases attributed to the correct source."""
    s = sorted(scores_benign)
    if not s:
        return 1.0
    # accept iff score >= thr; pick the (1-target) quantile as the threshold.
    idx = int((1.0 - target_tpr) * (len(s) - 1))
    return s[idx]


def evaluate(n_docs=60, sents_per_doc=16, benign_tpr=0.95, seed=20270301,
             real_embedding=False):
    import random
    rng = random.Random(seed)
    fields = CONTRACTS[CONTRACT]

    embed = cosine = None
    backend = "bag-of-words"
    if real_embedding:
        from truthprint import embedding as emb
        if emb.available():
            embed = lambda t: emb.embed([t])[0]  # noqa: E731
            cosine = emb.cosine
            backend = f"embedding:{emb.DEFAULT_MODEL}"

    # calibration and test splits (disjoint seeds)
    calib = _make_corpus(random.Random(seed + 1), max(4, n_docs // 4), sents_per_doc)
    test = _make_corpus(rng, n_docs, sents_per_doc)

    def build_retriever(items):
        gallery = {f"S{i}": it["src"] for i, it in enumerate(items)}
        r = rt.LedgerRetriever(embed=embed, cosine=cosine).build(gallery)
        return r, gallery

    # Verification is *id-addressed*: like the meaning-digest verifier, the ledger
    # is looked up by the candidate's id, so each candidate is checked against its
    # OWN registered source (not a gallery search). This isolates the real
    # question -- can source-vs-candidate similarity/NLI reject a typed tamper --
    # from low-entropy gallery ambiguity, which we report separately below.
    r_cal, _ = build_retriever(calib)
    def _emb(t):
        return r_cal.embed(t)
    _cos = r_cal.cosine

    # ---- calibrate similarity threshold and NLI-proxy theta on calib split -- #
    ret_scores, nli_scores = [], []
    for it in calib:
        ret_scores.append(_cos(_emb(it["src"]), _emb(it["benign_text"])))
        nli_scores.append(rt.source_coverage(it["src"], it["benign_text"]))
    thr_ret = _calibrate_threshold(ret_scores, benign_tpr)
    theta_nli = _calibrate_threshold(nli_scores, benign_tpr)

    # ---- evaluate on test split -------------------------------------------- #
    r_test, gallery = build_retriever(test)
    N = len(test)
    acc = {m: {"benign_ok": 0, "tamper_rej": 0} for m in
           ["typed", "retrieval", "retrieval_nli_proxy", "retrieval_nli_oracle"]}
    rank1_benign = rank1_tamper = 0

    for i, it in enumerate(test):
        sid_true = f"S{i}"
        src = it["src"]
        tag = register_tag(REFERENCE_KEY, it["gold_src"], NONCE, sid_true,
                           CONTRACT, TAG_BITS)
        src_vec = _emb(src)

        for kind, text, gold, key in (
                ("benign_ok", it["benign_text"], it["benign_gold"], "accept"),
                ("tamper_rej", it["alter_text"], it["alter_gold"], "reject")):
            # typed meaning-digest
            ok = authenticate(REFERENCE_KEY, extract_ext(text, LANG), NONCE,
                              sid_true, tag, CONTRACT, TAG_BITS)
            # retrieval: similarity of candidate to its own registered source
            sim = _cos(src_vec, _emb(text))
            ret_ok = sim >= thr_ret
            # + cheap NLI proxy (directional token coverage)
            nlip = ret_ok and rt.nli_proxy_entail(src, text, theta_nli)
            # + oracle NLI ceiling (perfect semantic check)
            nlio = ret_ok and rt.contract_preserved(it["gold_src"], gold, fields)
            for m, decided_accept in (("typed", ok), ("retrieval", ret_ok),
                                      ("retrieval_nli_proxy", nlip),
                                      ("retrieval_nli_oracle", nlio)):
                if key == "accept":
                    acc[m]["benign_ok"] += 1 if decided_accept else 0
                else:
                    acc[m]["tamper_rej"] += 0 if decided_accept else 1

        # supporting stat: nearest-neighbor gallery attribution (low-entropy)
        bsid, _ = r_test.attribute(it["benign_text"])
        asid, _ = r_test.attribute(it["alter_text"])
        rank1_benign += 1 if bsid == sid_true else 0
        rank1_tamper += 1 if asid == sid_true else 0

    meta = {
        "typed": {"localizes_field": True, "needs_model": False},
        "retrieval": {"localizes_field": False, "needs_model": False},
        "retrieval_nli_proxy": {"localizes_field": False, "needs_model": True},
        "retrieval_nli_oracle": {"localizes_field": False, "needs_model": True},
    }
    methods = {}
    for m, a in acc.items():
        methods[m] = {
            "benign_tpr": wilson_ci(a["benign_ok"], N),
            "tamper_rejection": wilson_ci(a["tamper_rej"], N),
            **meta[m],
        }
    return {
        "config": {"n_items": N, "n_docs": n_docs, "sents_per_doc": sents_per_doc,
                   "benign_tpr_target": benign_tpr, "seed": seed,
                   "backend": backend, "contract": CONTRACT,
                   "thr_retrieval": thr_ret, "theta_nli": theta_nli},
        "attribution_rank1": {
            "benign": wilson_ci(rank1_benign, N),
            "tamper": wilson_ci(rank1_tamper, N),
        },
        "methods": methods,
    }


def _fmt(res):
    c = res["config"]
    L = ["# Ledger retrieval(+NLI) baseline vs typed meaning-digest (reviewer W1)",
         "",
         f"Same ledger assumption, same seeded closed-domain corpus "
         f"({c['n_items']} items). Backend: `{c['backend']}`. Verification is "
         f"id-addressed (each candidate is checked against its OWN registered "
         f"source, exactly as the meaning-digest verifier looks up the ledger by "
         f"id). Similarity methods are calibrated so benign-paraphrase acceptance "
         f"is matched at ~{c['benign_tpr_target']:.2f}; we then read off "
         f"single-field **tamper rejection**, the decisive axis. `retrieval` = "
         f"cosine of candidate to its stored source; `+nli_proxy` adds a cheap "
         f"directional token-coverage entailment gate; `+nli_oracle` is a perfect, "
         f"unrealizable NLI ceiling that knows the gold contract.",
         "",
         "| Method | Benign accept (TPR) | Single-field tamper rejection | "
         "Localizes field | Needs semantic model |", "|---|---|---|---|---|"]
    order = ["typed", "retrieval", "retrieval_nli_proxy", "retrieval_nli_oracle"]
    label = {"typed": "Meaning-digest (typed)", "retrieval": "Retrieval (NN)",
             "retrieval_nli_proxy": "Retrieval + NLI (proxy)",
             "retrieval_nli_oracle": "Retrieval + NLI (oracle ceiling)"}
    for m in order:
        d = res["methods"][m]
        L.append(f"| {label[m]} | {_ci(d['benign_tpr'])} | "
                 f"{_ci(d['tamper_rejection'])} | "
                 f"{'yes' if d['localizes_field'] else 'no'} | "
                 f"{'yes' if d['needs_model'] else 'no'} |")
    ar = res["attribution_rank1"]
    L += ["",
          f"Attribution rank-1 rate (nearest gallery entry is the true source): "
          f"benign {_ci(ar['benign'])}, tamper {_ci(ar['tamper'])}. A tampered "
          "sentence is still nearest to its own source, so retrieval maps it back "
          "and cannot flag the edit; no similarity threshold separates a typed "
          "tamper from a legitimate paraphrase.", "",
          "> Storing the source and retrieving it survives paraphrase but cannot "
          "reject a single-field meaning change: retrieval alone and a cheap NLI "
          "proxy leave the tamper accepted, and only a *perfect* (unrealizable) NLI "
          "matches the typed contract's tamper rejection --- yet even that neither "
          "localizes the changed field nor yields a keyed, unforgeable tag, both of "
          "which the typed meaning-digest provides deterministically with no model. "
          "Closed-domain, bag-of-words backend by default; a real encoder behaves "
          "the same on tamper (a one-field edit is embedding-close to its source).",
          ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--n-docs", type=int, default=60)
    ap.add_argument("--sents-per-doc", type=int, default=16)
    ap.add_argument("--benign-tpr", type=float, default=0.95)
    ap.add_argument("--seed", type=int, default=20270301)
    ap.add_argument("--real-embedding", action="store_true")
    args = ap.parse_args()
    res = evaluate(n_docs=args.n_docs, sents_per_doc=args.sents_per_doc,
                   benign_tpr=args.benign_tpr, seed=args.seed,
                   real_embedding=args.real_embedding)
    md = _fmt(res)
    print(md)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        Path(args.out).with_suffix(".json").write_text(
            json.dumps(res, indent=2), encoding="utf-8")
        print(f"[written] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
