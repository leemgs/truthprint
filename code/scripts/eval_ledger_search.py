#!/usr/bin/env python3
"""Id-free ledger search: false attribution when the verifier has no doc id.

``eval_provenance.py`` measures *id-addressed* verification: the verifier is
told which registered sentence to test a translated sentence against, and its
false-positive column tests a single other sentence. A deployed verifier that
receives only a translated document has no id (translation strips any in-text
identifier), so it must search the ledger. Each extra ledger entry is another
chance for a contract collision, so false attribution grows with ledger size.

This script measures that setting on the same committed real NLLB run, with the
same Stage-2 extractor, keyed tags and >= 50% document rule:

  * sentence-level search: a translated sentence "matches" the ledger if it
    authenticates against ANY registered sentence; we report how often it
    matches at least one *wrong* sentence (other documents' 800 - 16 entries);
  * document-level search: a translated document is attributed to registered
    document d if >= 50% of its sentences authenticate against some sentence of
    d (unordered, since the verifier does not know the alignment). We report the
    id-free true-attribution rate (own document) and the false-attribution rate
    over all (translated doc, other registered doc) pairs, plus the fraction of
    translated documents attributed to at least one wrong document.

Usage: python3 scripts/eval_ledger_search.py ../paper/results/realmt_b2 [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_provenance import REFERENCE_KEY, TAG_BITS, _LANG, _read_jsonl  # noqa: E402
from truthprint.multilingual import extract_invariants, FIELDS  # noqa: E402
from truthprint.provenance import CONTRACTS, register_tag, authenticate  # noqa: E402
from truthprint.stats import wilson_ci  # noqa: E402

NONCE = b"prov-nonce-01"
MIN_FRACTION = 0.5


def evaluate(folder: str) -> dict:
    base = Path(folder)
    gold, docs = {}, defaultdict(list)
    for r in _read_jsonl(base / "01_source_items.jsonl"):
        for f in r["facts"]:
            gold[f["sent_id"]] = {k: f[k] for k in FIELDS}
            docs[r["doc_id"]].append(f["sent_id"])
    by_cond = defaultdict(lambda: defaultdict(dict))  # cond -> doc -> sid -> obs
    for t in _read_jsonl(base / "02_transformations.jsonl"):
        tag = t["transform_id"].rsplit("-", 1)[1]
        if tag in _LANG and t["sent_id"] in gold:
            by_cond[tag][t["doc_id"]][t["sent_id"]] = extract_invariants(
                t["output_text"], _LANG[tag])

    out = {"tag_bits": TAG_BITS, "ledger_docs": len(docs),
           "ledger_sentences": len(gold), "contracts": {}}
    for cname in CONTRACTS:
        reg = {sid: register_tag(KEY, g, NONCE, sid, cname, TAG_BITS)
               for sid, g in gold.items()}
        conds = {}
        for cond, tdocs in sorted(by_cond.items()):
            sent_wrong = sent_n = 0
            own_ok = pair_false = pair_n = docs_with_false = 0
            for d_obs, obs_sents in tdocs.items():
                # which registered sentences each translated sentence matches
                matches = {sid: {r for r in gold
                                 if authenticate(KEY, obs, NONCE, r, reg[r],
                                                 cname, TAG_BITS)}
                           for sid, obs in obs_sents.items()}
                for sid, m in matches.items():
                    sent_n += 1
                    sent_wrong += any(docs_of[r] != d_obs for r in m)
                any_false = False
                for d_reg, reg_sents in docs.items():
                    hit = sum(1 for m in matches.values() if m & set(reg_sents))
                    attributed = hit / len(matches) >= MIN_FRACTION
                    if d_reg == d_obs:
                        own_ok += attributed
                    else:
                        pair_n += 1
                        pair_false += attributed
                        any_false |= attributed
                docs_with_false += any_false
            n_docs = len(tdocs)
            conds[cond] = {
                "lang": _LANG[cond],
                "sentence_matches_wrong_entry": wilson_ci(sent_wrong, sent_n),
                "doc_true_attribution_id_free": wilson_ci(own_ok, n_docs),
                "doc_false_attribution_per_pair": wilson_ci(pair_false, pair_n),
                "docs_with_any_false_attribution": wilson_ci(docs_with_false, n_docs),
                "n_docs": n_docs, "n_pairs": pair_n, "n_sent": sent_n,
            }
        out["contracts"][cname] = {"fields": CONTRACTS[cname], "conditions": conds}
    return out


def independence_model(fp_path: Path, doc_len: int = 16) -> dict:
    """Predicted id-free false attribution per document pair if sentence
    records were independent draws at the measured contract-collision floor p
    (``semantic_fp.json``): a sentence matches some sentence of a 16-sentence
    document with q = 1-(1-p)^16, and a pair is falsely attributed when at
    least half of the sentences match, P[Bin(16, q) >= 8]."""
    from math import comb
    fp = json.loads(fp_path.read_text(encoding="utf-8"))["contracts"]
    out = {}
    for cname, c in fp.items():
        p = c["collision_prob"]
        q = 1 - (1 - p) ** doc_len
        need = -(-doc_len // 2)
        pair = sum(comb(doc_len, k) * q ** k * (1 - q) ** (doc_len - k)
                   for k in range(need, doc_len + 1))
        out[cname] = {"collision_floor": p, "sentence_hits_doc": q,
                      "false_attribution_per_pair": pair,
                      "ledger_docs_per_expected_false_attribution": (1 / pair) if pair else None}
    return out


def _ci(d) -> str:
    point, lo, hi = d
    return f"{point:.3f} [{lo:.3f},{hi:.3f}]"


def render(res: dict) -> str:
    lines = ["# Id-free ledger search on real MT output", "",
             f"The verifier receives only a translated document and searches the whole "
             f"ledger ({res['ledger_docs']} documents, {res['ledger_sentences']} sentences) "
             f"with the same Stage-2 extractor, {res['tag_bits']}-bit keyed tags and "
             f">= 50% document rule as `eval_provenance.py`, but with no document or "
             f"sentence id. Wilson 95% CI.", ""]
    for cname, c in res["contracts"].items():
        lines += [f"## Contract `{cname}` = {c['fields']}", "",
                  "| Condition | Sentence matches a wrong entry | Doc true attribution (id-free) "
                  "| Doc false attribution per pair | Docs with any false attribution |",
                  "|---|---|---|---|---|"]
        for cond, d in c["conditions"].items():
            lines.append(f"| {cond} ({d['lang']}) | {_ci(d['sentence_matches_wrong_entry'])} | "
                         f"{_ci(d['doc_true_attribution_id_free'])} | "
                         f"{_ci(d['doc_false_attribution_per_pair'])} (n={d['n_pairs']}) | "
                         f"{_ci(d['docs_with_any_false_attribution'])} |")
        lines.append("")
    if "independence_model" in res:
        lines += ["## Independence model (prediction, not a measurement)", "",
                  "| Contract | Collision floor p | Sentence hits a 16-sentence doc | "
                  "False attribution per pair | Ledger docs per expected false attribution |",
                  "|---|---|---|---|---|"]
        for cname, m in res["independence_model"].items():
            lines.append(f"| {cname} | {m['collision_floor']:.3g} | {m['sentence_hits_doc']:.3g} | "
                         f"{m['false_attribution_per_pair']:.2g} | "
                         f"{m['ledger_docs_per_expected_false_attribution']:.2g} |")
        lines.append("")
    lines += ["> Sentence-level search is not usable on its own: with a per-pair contract-"
              "collision floor near 1/192, a sentence collides with some wrong entry of a "
              "large ledger. The document rule is what keeps id-free attribution specific; "
              "the per-pair rate is the quantity that scales with ledger size.", ""]
    return "\n".join(lines)


KEY = REFERENCE_KEY
docs_of: dict[str, str] = {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", default=None, help="write <out>.json and <out>.md")
    args = ap.parse_args()
    for r in _read_jsonl(Path(args.folder) / "01_source_items.jsonl"):
        for f in r["facts"]:
            docs_of[f["sent_id"]] = r["doc_id"]
    res = evaluate(args.folder)
    fp_path = Path(args.folder).parent / "semantic_fp.json"
    if fp_path.exists():
        res["independence_model"] = independence_model(fp_path)
    md = render(res)
    if args.out:
        Path(args.out + ".json").write_text(json.dumps(res, indent=2), encoding="utf-8")
        Path(args.out + ".md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
