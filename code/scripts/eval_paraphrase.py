#!/usr/bin/env python3
"""Measure paraphrase and adaptive-attack robustness (RQ4 / RQ7, Eq. validremoval).

The paper's robustness evidence so far is all real *machine translation*; the
motivation, threat model, and hypotheses also claim robustness to
*paraphrasing*, which had never been measured. This harness closes that gap on
real English sentence strings, fully offline and seeded (same discipline as the
challenge set), by paraphrasing each closed-domain watermarked sentence and
re-running the surviving meaning-digest provenance authentication
(:mod:`truthprint.provenance`) on the paraphrase.

Three operator families (see :mod:`truthprint.paraphrase`):

  * **benign**   -- meaning-preserving, in-lexicon (voice, time reflow, verb/time
                    synonyms the extractor knows, discourse hedge). Authentication
                    SHOULD survive: this is RQ4 (paraphrase robustness).
  * **adaptive** -- meaning-preserving but schema-aware (RQ7): the attacker swaps
                    the predicate verb and time expression for *out-of-lexicon*
                    synonyms. Meaning is preserved (an oracle confirms the gold
                    contract is unchanged), so any authentication failure is a
                    ``ValidRemoval`` (Eq. validremoval): the watermark removed
                    without altering meaning.
  * **altering** -- one locked field changed. Authentication SHOULD fail (tamper
                    rejection); because meaning changed it is NOT a ValidRemoval.

Reported per operator (Wilson 95% CIs): authentication TPR, document-level
attribution, ValidRemoval rate, tamper rejection, mean surface distance, and the
Stage-1 *surface-carrier* recovery rate (the paraphrase counterpart of the 0/192
translation negative). The headline is that benign paraphrase is authenticated at
high rates while the adaptive attacker's residual success is bounded by the
*closed lexicon's coverage* (localized to the predicate/time fields it strips),
not by the meaning-digest principle -- exactly what the wide-coverage neural
frontend is meant to close.

Usage: python3 scripts/eval_paraphrase.py [--out PATH] [--n-docs N]
                                          [--sents-per-doc S] [--seed SEED]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthprint import challenge as ch
from truthprint import paraphrase as pp
from truthprint.multilingual import extract_invariants as extract_closed
from truthprint.multilingual_ext import extract_invariants as extract_extended
from truthprint.provenance import CONTRACTS, register_tag, authenticate, \
    document_attribution
from truthprint.stats import wilson_ci, bootstrap_ci

REFERENCE_KEY = b"truthprint-challenge-key-01234567"[:32]
NONCE = b"paraphrase-nonce-01"
TAG_BITS = 32
LANG = "en"


def _ci(x):
    return f"{x[0]:.3f} [{x[1]:.3f},{x[2]:.3f}]"


def evaluate(n_docs: int = 200, sents_per_doc: int = 16, seed: int = 20270201,
             contracts=("core6", "robust7", "full9"),
             num_resamples: int = 2000, extractor=extract_closed,
             frontend: str = "closed") -> dict:
    """Run the paraphrase/adaptive harness with a given invariant ``extractor``.

    ``extractor(text, lang) -> dict`` is the frontend under test: the closed
    Stage-2 lexicon (default), the extended-coverage frontend, or any neural
    ``extract`` callable. The corpus is seeded so closed and extended frontends
    see identical text, making the two runs a controlled defense comparison.
    """
    import random
    rng = random.Random(seed)

    # Pre-generate the corpus once so every contract/frontend sees identical text.
    # Each doc: list of (fact, (vbit,tbit), ref, variants, novel_variant).
    corpus = []
    for _ in range(n_docs):
        facts = [ch.sample_fact(rng) for _ in range(sents_per_doc)]
        doc = []
        for f in facts:
            vbit, tbit = rng.randrange(2), rng.randrange(2)
            ref = ch.realize(f, vbit, tbit)
            variants = {v["op"]: v for v in pp.paraphrase_variants(f, vbit, tbit, rng)}
            novel = pp.novel_adaptive_variant(f, vbit, tbit, rng)
            doc.append((f, (vbit, tbit), ref, variants, novel))
        corpus.append(doc)

    out = {"config": {"n_docs": n_docs, "sents_per_doc": sents_per_doc,
                      "seed": seed, "tag_bits": TAG_BITS, "lang": LANG,
                      "frontend": frontend},
           "contracts": {}}

    all_ops = pp.OPERATORS + ["adv_novel"]

    for cname in contracts:
        fields = CONTRACTS[cname]
        acc = {op: {"n": 0, "auth": 0, "vr": 0, "mp_n": 0, "tamper_rej": 0,
                    "tamper_n": 0, "surf_ok": 0, "cos": [],
                    "lit_vr": 0, "doc_flags": [], "miss": Counter()}
               for op in all_ops}

        for di, doc in enumerate(corpus):
            # register per-sentence tags over the ORIGINAL gold contract
            tags = [register_tag(REFERENCE_KEY, ch.ext_invariants(f), NONCE,
                                 f"D{di}-s{i}", cname, TAG_BITS)
                    for i, (f, *_rest) in enumerate(doc)]
            per_op_flags = defaultdict(list)
            for i, (f, (vbit, tbit), ref, variants, novel) in enumerate(doc):
                gold = ch.ext_invariants(f)
                ref_obs = extractor(ref, LANG)  # for literal Eq.4
                sid = f"D{di}-s{i}"
                items = list(variants.values()) + [novel]
                for v in items:
                    op = v["op"]
                    obs = extractor(v["text"], LANG)
                    ok = authenticate(REFERENCE_KEY, obs, NONCE, sid, tags[i],
                                      cname, TAG_BITS)
                    a = acc[op]
                    a["n"] += 1
                    a["auth"] += 1 if ok else 0
                    a["cos"].append(ch.cosine_bow(ref, v["text"]))
                    per_op_flags[op].append(ok)
                    # surface-carrier (Stage-1) recovery under paraphrase
                    try:
                        pf, car = ch.parse(v["text"])
                        surf_ok = (pf == f and car[0][0] == vbit
                                   and car[1][0] == tbit)
                    except Exception:  # noqa: BLE001 - unparseable surface = erasure
                        surf_ok = False
                    a["surf_ok"] += 1 if surf_ok else 0
                    # meaning-preserving (oracle) vs altering
                    if v["mode"] in ("benign", "adaptive"):
                        a["mp_n"] += 1
                        if not ok:
                            a["vr"] += 1  # ValidRemoval: meaning kept, detection lost
                            for kf in fields:
                                if obs.get(kf) != gold.get(kf):
                                    a["miss"][kf] += 1
                        # literal Eq.4: parser-based InvariantEq over the contract
                        inv_eq_parser = all(ref_obs.get(kf) == obs.get(kf)
                                            for kf in fields)
                        if (not ok) and inv_eq_parser:
                            a["lit_vr"] += 1
                    else:  # altering
                        a["tamper_n"] += 1
                        if not ok:
                            a["tamper_rej"] += 1
            for op in all_ops:
                acc[op]["doc_flags"].append(per_op_flags[op])

        # summarize
        per_op = {}
        for op in all_ops:
            a = acc[op]
            docatt = sum(1 for flags in a["doc_flags"]
                         if document_attribution(flags, 0.5))
            row = {
                "mode": ("altering" if op == "alter"
                         else "adaptive" if (op in pp.ADAPTIVE_OPS
                                             or op == "adv_novel")
                         else "benign"),
                "n": a["n"],
                "auth_tpr": wilson_ci(a["auth"], a["n"]),
                "document_attribution": wilson_ci(docatt, len(a["doc_flags"])),
                "mean_surface_cosine": bootstrap_ci(a["cos"], num_resamples),
                "surface_carrier_recovery": wilson_ci(a["surf_ok"], a["n"]),
            }
            if op == "alter":
                row["tamper_rejection"] = wilson_ci(a["tamper_rej"], a["tamper_n"])
            else:
                row["valid_removal"] = wilson_ci(a["vr"], a["mp_n"])
                row["valid_removal_literalEq4"] = wilson_ci(a["lit_vr"], a["mp_n"])
                if a["miss"]:
                    row["removal_field_breakdown"] = dict(a["miss"].most_common())
            per_op[op] = row

        # family aggregates
        def agg(ops, num_key, den_key):
            num = sum(acc[o][num_key] for o in ops)
            den = sum(acc[o][den_key] for o in ops)
            return wilson_ci(num, den)

        out["contracts"][cname] = {
            "fields": fields,
            "per_operator": per_op,
            "aggregate": {
                "benign_auth_tpr": agg(pp.BENIGN_OPS, "auth", "n"),
                "benign_valid_removal": agg(pp.BENIGN_OPS, "vr", "mp_n"),
                "adaptive_auth_tpr": agg(pp.ADAPTIVE_OPS, "auth", "n"),
                "adaptive_valid_removal": agg(pp.ADAPTIVE_OPS, "vr", "mp_n"),
                "adaptive_valid_removal_literalEq4":
                    agg(pp.ADAPTIVE_OPS, "lit_vr", "mp_n"),
                "adaptive_novel_valid_removal":
                    wilson_ci(acc["adv_novel"]["vr"], acc["adv_novel"]["mp_n"]),
                "adaptive_novel_auth_tpr":
                    wilson_ci(acc["adv_novel"]["auth"], acc["adv_novel"]["n"]),
                "altering_tamper_rejection":
                    wilson_ci(acc["alter"]["tamper_rej"], acc["alter"]["tamper_n"]),
                "benign_surface_carrier_recovery":
                    agg(pp.BENIGN_OPS, "surf_ok", "n"),
                "adaptive_surface_carrier_recovery":
                    agg(pp.ADAPTIVE_OPS, "surf_ok", "n"),
            },
        }
    return out


def _per_op_table(c2: dict) -> list:
    L = ["| Operator | Mode | Auth TPR | Doc attribution | ValidRemoval | "
         "Surface-carrier | Mean cosine |", "|---|---|---|---|---|---|---|"]
    for op, r in c2["per_operator"].items():
        if op == "alter":
            vr_label = f"{_ci(r['tamper_rejection'])} (tamper rej.)"
        else:
            vr_label = _ci(r["valid_removal"])
        L.append(f"| {op} | {r['mode']} | {_ci(r['auth_tpr'])} | "
                 f"{_ci(r['document_attribution'])} | {vr_label} | "
                 f"{_ci(r['surface_carrier_recovery'])} | "
                 f"{_ci(r['mean_surface_cosine'])} |")
    return L


def _fmt(res: dict) -> str:
    c = res["config"]
    fe = c.get("frontend", "closed")
    L = [f"### Frontend `{fe}` (contract `core6`)", ""]
    for cname, c2 in res["contracts"].items():
        if cname != "core6":
            continue
        L += _per_op_table(c2)
        brk = {}
        for op in ("adv_verb", "adv_time", "adv_combo", "adv_novel"):
            b = c2["per_operator"][op].get("removal_field_breakdown")
            if b:
                for k, v in b.items():
                    brk[k] = brk.get(k, 0) + v
        if brk:
            items = ", ".join(f"{k}: {v}" for k, v in
                              sorted(brk.items(), key=lambda kv: -kv[1]))
            L += ["", f"Residual adaptive-removal field breakdown "
                      f"(fields the `{fe}` frontend failed to recover): {items}."]
        L.append("")
    return "\n".join(L)


def _fmt_defense(closed: dict, ext: dict) -> str:
    c = closed["config"]
    hc = closed["contracts"]["core6"]["aggregate"]
    he = ext["contracts"]["core6"]["aggregate"]
    L = ["# Paraphrase and adaptive-attack robustness + extended-lexicon defense "
         "(RQ4 / RQ7)", "",
         f"Closed-domain, offline, seeded: {c['n_docs']} documents of "
         f"{c['sents_per_doc']} watermarked sentences are paraphrased on real "
         "English strings; meaning-digest provenance authentication is re-run on "
         "each paraphrase. `ValidRemoval` (Eq. validremoval) = meaning preserved "
         "(oracle gold contract) AND detection lost. The **closed** frontend is "
         "the Stage-2 lexicon; the **extended** frontend widens the English "
         "predicate/time/attribution inventory (coverage, not tolerance). "
         "`adv_novel` is a held-out attack whose synonyms lie outside the extended "
         "inventory too (the honest coverage bound).", "",
         "## Headline: extended-lexicon frontend defends the adaptive attack", "",
         "| Metric (contract core6) | Closed frontend | Extended frontend |",
         "|---|---|---|",
         f"| Benign paraphrase auth TPR (RQ4) | {_ci(hc['benign_auth_tpr'])} | "
         f"{_ci(he['benign_auth_tpr'])} |",
         f"| **Adaptive ValidRemoval (RQ7)** | **{_ci(hc['adaptive_valid_removal'])}** "
         f"| **{_ci(he['adaptive_valid_removal'])}** |",
         f"| Adaptive auth TPR | {_ci(hc['adaptive_auth_tpr'])} | "
         f"{_ci(he['adaptive_auth_tpr'])} |",
         f"| Held-out novel ValidRemoval (coverage bound) | "
         f"{_ci(hc['adaptive_novel_valid_removal'])} | "
         f"{_ci(he['adaptive_novel_valid_removal'])} |",
         f"| Altering-edit tamper rejection | "
         f"{_ci(hc['altering_tamper_rejection'])} | "
         f"{_ci(he['altering_tamper_rejection'])} |",
         "",
         "Reading: the closed lexicon lets the schema-aware adaptive attacker "
         "remove the mark (high ValidRemoval), but the extended-coverage frontend "
         "recovers the same invariants and drives adaptive ValidRemoval to ~0 "
         "while **still rejecting tampers** (coverage widened, tolerance not) and "
         "keeping benign paraphrase authenticated. This is direct evidence that "
         "the vulnerability is closed-lexicon coverage, not the meaning-digest "
         "principle. The held-out `adv_novel` attack still succeeds under both "
         "frontends: any *fixed* lexicon is evadable by an out-of-inventory "
         "synonym, which is why the general answer is the open-vocabulary neural "
         "frontend (`truthprint.neural_parser`, e.g. via `APIBackend`); the "
         "extension quantifies the mechanism (each added synonym family recovers "
         "authentication for that family).", "",
         "## Per-operator detail", ""]
    L.append(_fmt(closed))
    L.append(_fmt(ext))
    L += ["> Extended coverage is still a fixed lexicon (held-out `adv_novel` "
          "removal stays high); the open-vocabulary neural frontend is the general "
          "defense. Closed-domain Stage-2; wide-coverage paraphrase robustness at "
          "scale remains future work.", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--n-docs", type=int, default=200)
    ap.add_argument("--sents-per-doc", type=int, default=16)
    ap.add_argument("--seed", type=int, default=20270201)
    ap.add_argument("--frontend", choices=["closed", "extended", "both"],
                    default="both", help="invariant frontend under test")
    ap.add_argument("--api-model", default=None,
                    help="optional: OpenAI-compatible model id for a real neural "
                         "frontend (open-vocabulary defense)")
    ap.add_argument("--api-base", default=None,
                    help="optional: OpenAI-compatible base URL for --api-model")
    args = ap.parse_args()

    extractors = {"closed": extract_closed, "extended": extract_extended}
    if args.api_model and args.api_base:
        from truthprint.neural_parser import NeuralInvariantExtractor, APIBackend
        neural = NeuralInvariantExtractor(
            APIBackend(model=args.api_model, base_url=args.api_base))
        extractors["neural"] = neural.extract

    kw = dict(n_docs=args.n_docs, sents_per_doc=args.sents_per_doc, seed=args.seed)
    if args.frontend == "both":
        closed = evaluate(extractor=extract_closed, frontend="closed", **kw)
        ext = evaluate(extractor=extract_extended, frontend="extended", **kw)
        md = _fmt_defense(closed, ext)
        payload = {"closed": closed, "extended": ext}
    else:
        one = evaluate(extractor=extractors[args.frontend],
                       frontend=args.frontend, **kw)
        md = _fmt(one)
        payload = {args.frontend: one}
    print(md)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        Path(args.out).with_suffix(".json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8")
        print(f"[written] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
