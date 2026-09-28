"""Tests for the paraphrase / adaptive-attack harness (RQ4 / RQ7).

These assert the properties the paper relies on:
  * paraphrase operators preserve the gold contract (the oracle meaning),
  * benign in-lexicon paraphrase is authenticated (RQ4),
  * the schema-aware adaptive attacker's residual success is localized to the
    closed lexicon's content fields (RQ7 / Eq. validremoval), while polarity and
    agent survive even the adaptive attack,
  * a meaning-altering edit is rejected (tamper), and
  * adaptive time phrases carry no _TIME lexicon marker (a fair attack).
"""
import random

from truthprint import paraphrase as pp
from truthprint import challenge as ch
from truthprint.multilingual import extract_invariants, _TIME
from truthprint.provenance import CONTRACTS, register_tag, authenticate

KEY = b"truthprint-challenge-key-01234567"[:32]
NONCE = b"paraphrase-nonce-01"


def _auth(text, gold_inv, contract="core6"):
    tag = register_tag(KEY, gold_inv, NONCE, "s1", contract, 32)
    obs = extract_invariants(text, "en")
    return authenticate(KEY, obs, NONCE, "s1", tag, contract, 32)


def test_operators_cover_expected_set():
    rng = random.Random(0)
    f = ch.sample_fact(rng)
    ops = {v["op"] for v in pp.paraphrase_variants(f, 0, 0, rng)}
    assert ops == set(pp.OPERATORS)
    assert set(pp.BENIGN_OPS) | set(pp.ADAPTIVE_OPS) | {"alter"} == set(pp.OPERATORS)


def test_adaptive_time_phrases_have_no_lexicon_marker():
    # A fair adaptive attack must strip the marker, not accidentally keep it.
    for direction, phrases in pp.ADAPTIVE_TIME.items():
        for phrase in phrases:
            low = phrase.lower()
            for markers in _TIME.values():
                for m in markers.get("en", []):
                    assert m not in low, f"{phrase!r} leaks time marker {m!r}"


def test_benign_paraphrase_preserves_meaning_and_authenticates():
    rng = random.Random(1)
    fields = CONTRACTS["core6"]
    ok = tot = 0
    for _ in range(200):
        f = ch.sample_fact(rng)
        gold = ch.ext_invariants(f)
        for v in pp.paraphrase_variants(f, rng.randrange(2), rng.randrange(2), rng):
            if v["mode"] != "benign":
                continue
            tot += 1
            # oracle: meaning preserved
            assert pp.invariant_eq_gold(f, v["gold"], fields)
            if _auth(v["text"], gold):
                ok += 1
    # benign paraphrase should authenticate essentially always
    assert ok / tot >= 0.99, f"benign auth rate {ok/tot:.3f}"


def test_adaptive_attack_removes_but_only_via_content_fields():
    rng = random.Random(2)
    fields = CONTRACTS["core6"]
    removed = tot = 0
    polarity_agent_kept = 0
    for _ in range(150):
        f = ch.sample_fact(rng)
        gold = ch.ext_invariants(f)
        for v in pp.paraphrase_variants(f, rng.randrange(2), rng.randrange(2), rng):
            if v["mode"] != "adaptive":
                continue
            tot += 1
            assert pp.invariant_eq_gold(f, v["gold"], fields)  # meaning preserved
            obs = extract_invariants(v["text"], "en")
            if not authenticate(KEY, obs, NONCE, "s1",
                                register_tag(KEY, gold, NONCE, "s1", "core6", 32),
                                "core6", 32):
                removed += 1
            # polarity + agent (function-word / reference markers) survive the
            # content-word attack: the attacker cannot strip them without
            # changing meaning.
            if obs.get("polarity") == gold["polarity"] and \
               obs.get("agent") == gold["agent"]:
                polarity_agent_kept += 1
    assert removed / tot >= 0.9, f"adaptive ValidRemoval {removed/tot:.3f}"
    assert polarity_agent_kept == tot, "polarity/agent must survive adaptive attack"


def test_altering_edit_is_rejected():
    rng = random.Random(3)
    rej = tot = 0
    for _ in range(200):
        f = ch.sample_fact(rng)
        gold = ch.ext_invariants(f)
        for v in pp.paraphrase_variants(f, rng.randrange(2), rng.randrange(2), rng):
            if v["op"] != "alter":
                continue
            tot += 1
            # meaning changed -> not a valid removal
            assert not pp.invariant_eq_gold(f, v["gold"], CONTRACTS["core6"])
            if not _auth(v["text"], gold):
                rej += 1
    assert rej / tot >= 0.99, f"tamper rejection {rej/tot:.3f}"


def test_eval_paraphrase_smoke_and_determinism():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "eval_paraphrase",
        Path(__file__).resolve().parent.parent / "scripts" / "eval_paraphrase.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    r1 = mod.evaluate(n_docs=15, sents_per_doc=8, contracts=("core6",),
                      num_resamples=200)
    r2 = mod.evaluate(n_docs=15, sents_per_doc=8, contracts=("core6",),
                      num_resamples=200)
    assert r1 == r2, "evaluation must be deterministic under a fixed seed"
    agg = r1["contracts"]["core6"]["aggregate"]
    assert agg["benign_auth_tpr"][0] >= 0.99
    assert agg["adaptive_valid_removal"][0] >= 0.9
    assert agg["altering_tamper_rejection"][0] >= 0.99
    # literal Eq.4 ValidRemoval is ~0 by construction for a meaning-digest
    assert agg["adaptive_valid_removal_literalEq4"][0] == 0.0
