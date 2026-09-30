"""Tests for the ledger retrieval(+NLI) baseline (reviewer W1).

Assert the decisive contrast: under the same ledger assumption, storing the
source and verifying by similarity/NLI attributes a transformed sentence back to
its source (benign accept) but cannot reject a single-field typed tamper unless a
*perfect* (oracle) NLI is assumed, whereas the typed meaning-digest rejects it
deterministically. Also check the retrieval mechanics and that a single-field
tamper is at least as retrievable to its source as a benign paraphrase (so no
similarity threshold separates them).
"""
import importlib.util
from pathlib import Path

from truthprint import retrieval as rt
from truthprint import challenge as ch


def _load_eval():
    spec = importlib.util.spec_from_file_location(
        "eval_retrieval",
        Path(__file__).resolve().parent.parent / "scripts" / "eval_retrieval.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_retriever_attributes_exact_source():
    r = rt.LedgerRetriever().build({"a": "the developer fixed the server error.",
                                    "b": "the analyst fixed the cache miss."})
    sid, sim = r.attribute("the developer fixed the server error.")
    assert sid == "a" and sim > 0.99


def test_source_coverage_drops_when_a_source_token_is_removed():
    # a paraphrase keeps content tokens; a negation/number edit drops/changes one
    src = "the developer fixed two server errors"
    para = "two server errors were fixed by the developer"
    assert rt.source_coverage(src, para) >= 0.9
    assert rt.source_coverage(src, "the developer fixed five server errors") < 1.0


def test_contract_preserved_oracle():
    f = ch.sample_fact(__import__("random").Random(0))
    g = ch.ext_invariants(f)
    from truthprint.provenance import CONTRACTS
    fields = CONTRACTS["core6"]
    assert rt.contract_preserved(g, dict(g), fields)
    g2 = dict(g)
    g2["polarity"] = "negative" if g["polarity"] == "positive" else "positive"
    assert not rt.contract_preserved(g, g2, fields)


def test_eval_retrieval_decisive_contrast_and_determinism():
    mod = _load_eval()
    r1 = mod.evaluate(n_docs=30, sents_per_doc=12, seed=20270301)
    r2 = mod.evaluate(n_docs=30, sents_per_doc=12, seed=20270301)
    assert r1 == r2, "evaluation must be deterministic under a fixed seed"
    m = r1["methods"]
    # typed contract: accepts paraphrase, rejects tamper, no model, localizes
    assert m["typed"]["benign_tpr"][0] >= 0.99
    assert m["typed"]["tamper_rejection"][0] >= 0.99
    assert m["typed"]["localizes_field"] is True
    assert m["typed"]["needs_model"] is False
    # retrieval + cheap NLI: matched benign acceptance but cannot reject the tamper
    assert m["retrieval"]["benign_tpr"][0] >= 0.85
    assert m["retrieval"]["tamper_rejection"][0] <= 0.2
    assert m["retrieval_nli_proxy"]["tamper_rejection"][0] <= 0.3
    # only the perfect (unrealizable) NLI ceiling matches typed tamper rejection
    assert m["retrieval_nli_oracle"]["tamper_rejection"][0] >= 0.99
    assert m["retrieval_nli_oracle"]["localizes_field"] is False
    # a single-field tamper is at least as retrievable to its source as a paraphrase
    ar = r1["attribution_rank1"]
    assert ar["tamper"][0] >= ar["benign"][0]
