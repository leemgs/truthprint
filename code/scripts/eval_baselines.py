#!/usr/bin/env python3
"""Fill the paper's comparison tables (Table V clean-text, Table VI translation)
for Truthprint and the four baselines, measured on the shared Stage-1 testbed.

Every method faces the identical meaning-preserving channel characterised by
``(tau_tok, eps_inv)`` and is scored with the identical protocol:

  * calibrate a decision threshold at 1% FPR on null (un-watermarked) documents;
  * measure TPR at that threshold after the channel;
  * ROC-AUC from watermarked vs null score populations.

Truthprint is run through its real linguistic codec (actual sentences); the
baselines through the faithful ``truthprint.baselines`` reductions. The relative
translation ordering is *derived* from where each method places its signal --
token identity (KGW/SynthID, DEW), sentence embedding (SemStamp), or meaning
structure (SWAN, Truthprint) -- not chosen per method.

Run:  python3 scripts/eval_baselines.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint.baselines import (Document, make_document, channel,
    KGWGreenList, DEWEditRobust, SemStampLSH, SWANStructural)
from truthprint.linguistic import (Fact, LinguisticCodec,
    invariant_preserving_transform)

# ---- shared configuration ------------------------------------------------- #
N_DOCS = 500
N_SENT = 32
TOKS_PER_SENT = 8
KEY = b"truthprint-demo-key-0123456789abc"

# translation channels: (label, tau_tok, eps_inv)
#   tau_tok -- surface tokens replaced (cross-script translation ~= all tokens)
#   eps_inv -- meaning carriers lost to parse normalisation (paper's Table VI)
TRANSLATION = [
    ("EN->KO", 0.92, 0.30),
    ("EN->HI", 0.95, 0.35),
    ("KO->EN", 0.90, 0.28),
]

AGENTS = ["the developer", "the auditor", "the operator", "the vendor",
          "the engineer", "the administrator", "the analyst", "the reviewer"]
PATIENTS = ["the server error", "the config drift", "the data leak",
            "the build failure", "the memory leak", "the security flaw",
            "the network issue", "the database bug"]


# ---- metric helpers ------------------------------------------------------- #
def roc_auc(pos, neg):
    wins = sum(p > q for p in pos for q in neg)
    ties = sum(p == q for p in pos for q in neg)
    return (wins + 0.5 * ties) / (len(pos) * len(neg))


def threshold_at_fpr(neg, fpr=0.01):
    """Lowest threshold whose null pass-rate is <= fpr.

    The added epsilon keeps scores equal to the null mass (e.g. a detector that
    collapses to exactly 0 under an over-budget transform) on the reject side,
    so an over-budget positive that is indistinguishable from null does not pass.
    """
    s = sorted(neg, reverse=True)
    k = int(fpr * len(s))
    base = s[k] if k < len(s) else s[-1]
    return base + 1e-6


def tpr_at(pos, thr):
    return sum(1 for p in pos if p >= thr) / len(pos)


# ---- baseline evaluation on the shared Document abstraction ---------------- #
def eval_baseline(method, seed):
    rng = random.Random(seed)
    # null population (un-watermarked) for threshold + AUC
    neg = [method.score(make_document(N_SENT, TOKS_PER_SENT, rng), KEY)
           for _ in range(N_DOCS)]
    thr = threshold_at_fpr(neg, 0.01)

    # clean watermarked population
    pos_clean = []
    for _ in range(N_DOCS):
        base = make_document(N_SENT, TOKS_PER_SENT, rng)
        pos_clean.append(method.score(method.embed(base, KEY), KEY))

    tpr_clean = tpr_at(pos_clean, thr)
    auc = roc_auc(pos_clean, neg)

    trans = {}
    for label, tau, eps in TRANSLATION:
        hits = []
        for _ in range(N_DOCS):
            base = make_document(N_SENT, TOKS_PER_SENT, rng)
            wm = method.embed(base, KEY)
            got = channel(wm, tau, eps, rng)
            hits.append(method.score(got, KEY))
        trans[label] = tpr_at(hits, thr)
    return tpr_clean, auc, trans


# ---- Truthprint evaluation on the real linguistic codec -------------------- #
def eval_truthprint(seed):
    rng = random.Random(seed)
    codec = LinguisticCodec(KEY, n_sentences=N_SENT, msg_len=12, tag_bits=20)

    def make_facts():
        return [Fact(rng.choice(AGENTS), rng.choice(PATIENTS))
                for _ in range(N_SENT)]

    # null: text authored without the key (wrong nonce at detect)
    neg = []
    for _ in range(N_DOCS):
        facts = make_facts()
        sents = codec.encode(facts, [rng.randint(0, 1) for _ in range(12)],
                             codec.core.new_nonce())
        neg.append(codec.detect(sents, codec.core.new_nonce()).z_score)
    thr = threshold_at_fpr(neg, 0.01)

    # clean watermarked
    pos, bleu = [], []
    for _ in range(N_DOCS):
        facts = make_facts()
        msg = [rng.randint(0, 1) for _ in range(12)]
        nonce = codec.core.new_nonce()
        sents = codec.encode(facts, msg, nonce)
        pos.append(codec.detect(sents, nonce).z_score)
        # BLEU-1 surface-preservation vs an unconstrained realization
        plain = codec.encode(facts, [rng.randint(0, 1) for _ in range(12)],
                             codec.core.new_nonce())
        overlap = 0
        for a, b in zip(sents, plain):
            at, bt = a.lower().split(), b.lower().split()
            overlap += sum(1 for t in at if t in bt) / max(1, len(at))
        bleu.append(overlap / N_SENT)

    tpr_clean = tpr_at(pos, thr)
    auc = roc_auc(pos, neg)
    mean_bleu = sum(bleu) / len(bleu)

    trans = {}
    for label, _tau, eps in TRANSLATION:
        hits = []
        for _ in range(N_DOCS):
            facts = make_facts()
            msg = [rng.randint(0, 1) for _ in range(12)]
            nonce = codec.core.new_nonce()
            sents = codec.encode(facts, msg, nonce)
            transformed, reliability = [], []
            for s in sents:
                t, rel = invariant_preserving_transform(s, rng, eps)
                transformed.append(t)
                reliability.append(rel)
            hits.append(codec.detect(transformed, nonce, reliability).z_score)
        trans[label] = tpr_at(hits, thr)
    return tpr_clean, auc, mean_bleu, trans


# ---- run ------------------------------------------------------------------ #
def main():
    print(f"Shared Stage-1 testbed: {N_DOCS} docs x {N_SENT} sentences x "
          f"{TOKS_PER_SENT} tokens; threshold @ 1% FPR.\n")

    rows = []  # (name, tpr_clean, auc, quality, {label: tpr})

    methods = [
        ("SynthID-Text/KGW", KGWGreenList(), 2001),
        ("DEW",              DEWEditRobust(), 2002),
        ("SemStamp",         SemStampLSH(),   2003),
        ("SWAN",             SWANStructural(), 2004),
    ]
    for name, m, seed in methods:
        tpr_clean, auc, trans = eval_baseline(m, seed)
        rows.append((name, tpr_clean, auc, None, trans))

    tp_clean, tp_auc, tp_bleu, tp_trans = eval_truthprint(2005)
    rows.append(("Truthprint", tp_clean, tp_auc, tp_bleu, tp_trans))

    print("=== TABLE V: clean-text detection ===")
    print(f"{'Method':20} {'TPR@1%FPR':>10} {'ROC-AUC':>9} {'Quality':>9}")
    for name, tpr, auc, q, _ in rows:
        qs = f"{q:.2f}" if q is not None else "  --"
        print(f"{name:20} {tpr:>10.3f} {auc:>9.3f} {qs:>9}")

    print("\n=== TABLE VI: translation-robustness (TPR @ 1% FPR) ===")
    hdr = "".join(f"{lab:>10}" for lab, _, _ in TRANSLATION)
    print(f"{'Method':20}{hdr}")
    for name, _, _, _, trans in rows:
        cells = "".join(f"{trans[lab]:>10.3f}" for lab, _, _ in TRANSLATION)
        print(f"{name:20}{cells}")


if __name__ == "__main__":
    main()
