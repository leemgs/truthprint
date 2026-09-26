"""Tests for the wide-coverage neural invariant extractor (W5).

All offline: the LLM is a deterministic stub, so these check the prompt, the
robust JSON parsing/normalization, the drop-in extractor interface, and the
scorer arithmetic -- not model quality.
"""
import json

from truthprint.multilingual import FIELDS
from truthprint.neural_parser import (build_prompt, parse_response,
                                      normalize_fields, NeuralInvariantExtractor,
                                      StubBackend)
from scripts.eval_neural_parser import score


def test_prompt_mentions_all_fields():
    p = build_prompt("The developer fixed the server error.", "en")
    for f in FIELDS:
        assert f in p


def test_parse_plain_json():
    raw = ('{"agent":"the developer","patient":"server error","predicate":"fix",'
           '"polarity":"positive","quantity":1,"time_dir":"before",'
           '"modality":"must","attribution":"none","causation":"because"}')
    d = parse_response(raw)
    assert d["predicate"] == "FIX"          # uppercased
    assert d["time_dir"] == "previous"      # before -> previous
    assert d["modality"] == "necessary"     # must -> necessary
    assert d["causation"] == "cause"        # because -> cause
    assert d["quantity"] == 1


def test_parse_with_code_fence_and_prose():
    raw = ("Here is the JSON:\n```json\n"
           '{"agent":"the engineer","polarity":"negative","quantity":"three"}\n'
           "```\nHope this helps!")
    d = parse_response(raw)
    assert d["agent"] == "the engineer"
    assert d["polarity"] == "negative"
    assert d["quantity"] == 3               # word -> int
    # missing fields abstain (None), except defaulted modality/attr/causation
    assert d["patient"] is None
    assert d["modality"] == "asserted"


def test_parse_garbage_abstains():
    d = parse_response("I could not extract anything useful.")
    assert all(d[f] is None or f in ("polarity", "modality", "attribution", "causation")
               for f in FIELDS)


def test_extractor_with_stub_backend():
    reply = ('{"agent":"the operator","patient":"config drift","predicate":"FIX",'
             '"polarity":"positive","quantity":1,"time_dir":"following",'
             '"modality":"possible","attribution":"vendor","causation":"purpose"}')
    ext = NeuralInvariantExtractor(StubBackend({"config drift": reply}))
    d = ext.extract("On the following day the operator may fix config drift.", "en")
    assert d["patient"] == "config drift"
    assert d["modality"] == "possible"
    assert d["attribution"] == "vendor"
    # unmatched sentence -> stub returns {} -> abstentions
    d2 = ext.extract("Totally unrelated sentence.", "en")
    assert d2["agent"] is None


def test_scorer_field_and_domain_breakdown(tmp_path):
    gold = {"agent": "the developer", "patient": "server error", "predicate": "FIX",
            "polarity": "positive", "quantity": 1, "time_dir": "previous",
            "modality": "asserted", "attribution": "none", "causation": "none"}
    # neural gets everything right; lexicon (run on this English text) also should
    recs = [{
        "sent_id": "s1", "lang": "en", "condition": "clean", "domain": "template",
        "text": "The developer fixed the server error on the previous day.",
        "gold": gold, "pred": dict(gold),
    }]
    p = tmp_path / "out.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    from scripts.eval_neural_parser import _read_jsonl
    out = score(_read_jsonl(p))
    assert out["n_records"] == 1
    assert out["all_exact"]["neural"][0] == 1.0
    assert "template" in out["by_domain"]
    # neural polarity recovered
    assert out["fields"]["neural"]["polarity"][0] == 1.0
