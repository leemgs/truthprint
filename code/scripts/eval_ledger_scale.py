#!/usr/bin/env python3
"""Id-free ledger search at scale: false attribution against large ledgers.

``eval_ledger_search.py`` searches a ledger of the 50 registered documents.
Deployments register far more. Only the *queried* documents need translating,
so this script keeps the 50 translated query documents of the committed NLLB
run and grows the ledger with K distractor documents drawn from the same
generator as the corpus (``challenge.sample_fact`` / ``ext_invariants``) under
a different seed, i.e. independent registered documents with the corpus's own
(low-entropy) record distribution.

Matching is done on the contract record itself. A keyed tag verifies for a
candidate sentence id exactly when the extracted contract fields equal the
registered ones (up to a 2^-32 tag collision), so indexing the ledger by
contract record gives the same decisions as testing every tag and scales to
10^5 documents. ``--validate`` checks this against the tag-based 50-document
results of ``ledger_search.json``.

A query document is attributed to every registered document matched by at
least half of its sentences (a sentence matches a document if it equals any of
that document's 16 records; the verifier does not know the alignment).

Usage: python3 scripts/eval_ledger_scale.py ../paper/results/realmt_b2 \
           [--sizes 0 1000 10000 100000] [--out PATH] [--validate]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_provenance import _LANG, _read_jsonl  # noqa: E402
from truthprint import challenge as ch  # noqa: E402
from truthprint.multilingual import extract_invariants  # noqa: E402
from truthprint.provenance import CONTRACTS  # noqa: E402
from truthprint.stats import wilson_ci  # noqa: E402

SENTS = 16
MIN_FRACTION = 0.5
DISTRACTOR_SEED = 20261023  # the committed corpus used 20260924


def record(inv: dict, fields: list[str]) -> tuple:
    return tuple(inv.get(f) for f in fields)


def distractors(k: int, seed: int = DISTRACTOR_SEED) -> list[list[dict]]:
    rng = random.Random(seed)
    return [[ch.ext_invariants(ch.sample_fact(rng)) for _ in range(SENTS)] for _ in range(k)]


def evaluate(folder: str, sizes: list[int]) -> dict:
    base = Path(folder)
    real = {}  # doc_id -> [gold record dicts]
    for r in _read_jsonl(base / "01_source_items.jsonl"):
        real[r["doc_id"]] = [{k: v for k, v in f.items() if k != "sent_id"} for f in r["facts"]]
    queries = defaultdict(lambda: defaultdict(list))  # cond -> doc -> [extracted]
    for t in _read_jsonl(base / "02_transformations.jsonl"):
        tag = t["transform_id"].rsplit("-", 1)[1]
        if tag in _LANG:
            queries[tag][t["doc_id"]].append(extract_invariants(t["output_text"], _LANG[tag]))
    pool = distractors(max(sizes))
    out = {"query_docs": len(real), "distractor_seed": DISTRACTOR_SEED,
           "method": "contract-record index (equivalent to tag verification up to 2^-32)",
           "contracts": {}}
    for cname in ("core6", "full9"):
        fields = CONTRACTS[cname]
        by_size = {}
        for k in sizes:
            index = defaultdict(set)  # record -> set(doc ids)
            for d, recs in real.items():
                for g in recs:
                    index[record(g, fields)].add(d)
            for j in range(k):
                for g in pool[j]:
                    index[record(g, fields)].add(f"X{j:06d}")
            ledger_docs = len(real) + k
            conds = {}
            for cond, qdocs in sorted(queries.items()):
                own = false_total = docs_with_false = 0
                for d, sents in qdocs.items():
                    hits = Counter()
                    for inv in sents:
                        for doc in index.get(record(inv, fields), ()):
                            hits[doc] += 1
                    need = MIN_FRACTION * len(sents)
                    attributed = {doc for doc, c in hits.items() if c >= need}
                    own += d in attributed
                    false_here = len(attributed - {d})
                    false_total += false_here
                    docs_with_false += false_here > 0
                n = len(qdocs)
                pairs = n * (ledger_docs - 1)
                conds[cond] = {
                    "own_attribution": wilson_ci(own, n),
                    "docs_with_any_false_attribution": wilson_ci(docs_with_false, n),
                    "false_attributions": false_total, "pairs": pairs,
                    "false_attribution_per_pair": wilson_ci(false_total, pairs),
                }
            by_size[str(ledger_docs)] = conds
        out["contracts"][cname] = by_size
    return out


def render(res: dict) -> str:
    L = ["# Id-free ledger search at scale", "",
         f"{res['query_docs']} translated query documents per condition (committed NLLB run) "
         "searched against ledgers of the 50 registered documents plus K distractor "
         "documents drawn from the corpus generator (seed "
         f"{res['distractor_seed']}). Matching: {res['method']}. A query document is "
         "attributed to every registered document matched by >= 50% of its sentences. "
         "Wilson 95% CI.", ""]
    for cname, by_size in res["contracts"].items():
        L += [f"## Contract `{cname}`", "",
              "| Ledger docs | Condition | Own doc attributed | Query docs with a false attribution "
              "| False attributions / pairs |", "|---|---|---|---|---|"]
        for size, conds in by_size.items():
            for cond, c in conds.items():
                o, f = c["own_attribution"], c["docs_with_any_false_attribution"]
                L.append(f"| {int(size):,} | {cond} | {o[0]:.3f} | {f[0]:.3f} [{f[1]:.3f},{f[2]:.3f}] | "
                         f"{c['false_attributions']:,} / {c['pairs']:,} |")
        L.append("")
    return "\n".join(L)


def validate(res: dict, ledger_json: Path) -> None:
    """The 50-document ledger must reproduce the tag-based ledger_search.json."""
    ref = json.loads(ledger_json.read_text(encoding="utf-8"))["contracts"]
    for cname, by_size in res["contracts"].items():
        mine = by_size["50"]
        for cond, c in mine.items():
            r = ref[cname]["conditions"][cond]
            assert abs(c["own_attribution"][0] - r["doc_true_attribution_id_free"][0]) < 1e-9, (cname, cond)
            assert c["false_attributions"] == round(r["doc_false_attribution_per_pair"][0] * r["n_pairs"]), (cname, cond)
    print("[validate] 50-document ledger reproduces ledger_search.json exactly")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--sizes", type=int, nargs="+", default=[0, 1000, 10000, 100000])
    ap.add_argument("--out", default=None, help="write <out>.json and <out>.md")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    res = evaluate(args.folder, sorted(set(args.sizes)))
    if args.validate:
        validate(res, Path(args.folder).parent / "ledger_search.json")
    md = render(res)
    if args.out:
        Path(args.out + ".json").write_text(json.dumps(res, indent=2), encoding="utf-8")
        Path(args.out + ".md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
