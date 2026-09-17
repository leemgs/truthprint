"""Tests for the field-level semantic challenge set (Stage-1, closed domain).

These assert (a) the closed-domain parser exactly inverts realization over the
enumerated domain, so the experiment's numbers are trustworthy, and (b) the
qualitative ablation outcomes the paper reports: the typed invariant + MAC
contract detects every single-field tamper, decode-only (no MAC) detects none,
and an embedding-similarity gate calibrated to keep legitimate paraphrases
catches almost no tamper.
"""
import random

from truthprint import challenge as ch


def test_parser_roundtrips_over_enumerated_domain():
    bad = 0
    total = 0
    for agent in ch.AGENTS:
        for patient in ch.PATIENTS:
            for q in [1, 2, 3, 5, 8]:
                for pol in ["positive", "negative"]:
                    for td in ["previous", "following"]:
                        for mod in ["asserted", "necessary", "possible"]:
                            for attr in ["none", "report", "vendor"]:
                                for cause in ["none", "cause", "purpose"]:
                                    f = ch.ExtFact(agent, patient, q, pol, td,
                                                   mod, attr, cause)
                                    for v in (0, 1):
                                        for t in (0, 1):
                                            s = ch.realize(f, v, t)
                                            f2, car = ch.parse(s)
                                            total += 1
                                            if (f2 != f or car[0][0] != v
                                                    or car[1][0] != t):
                                                bad += 1
    assert bad == 0, f"{bad}/{total} round-trip failures"


def test_altering_edit_changes_exactly_one_field():
    rng = random.Random(1)
    for _ in range(200):
        f = ch.sample_fact(rng)
        for field in ch.FIELDS:
            f2 = ch.altering_edit(f, field, rng)
            diffs = [k for k in ch.ext_invariants(f)
                     if ch.ext_invariants(f)[k] != ch.ext_invariants(f2)[k]]
            assert diffs == [field], (field, diffs)


def test_cosine_altering_edit_stays_high():
    # a single-field meaning-altering edit is lexically small: cosine stays high
    rng = random.Random(2)
    f = ch.sample_fact(rng)
    ref = ch.realize(f, 0, 0)
    for field in ch.FIELDS:
        f2 = ch.altering_edit(f, field, rng)
        assert ch.cosine_bow(ref, ch.realize(f2, 0, 0)) > 0.8


def test_ablation_outcomes_smoke():
    r = ch.run_challenge(n_docs=60, num_resamples=200, seed=123)
    agg = r["aggregate"]
    # typed contract catches every tamper; decode-only catches none.
    assert agg["typed_tamper_detect"][0] == 1.0
    assert agg["nomac_tamper_detect"][0] == 0.0
    # embedding gate calibrated to keep paraphrases catches almost no tamper.
    assert agg["embed_tamper_detect"][0] < 0.1
    # attribution survives the benign paraphrase transform.
    assert r["benign"]["typed_retention"][0] >= 0.95
    # a large fraction of tampers look at least as similar as legit paraphrases.
    assert agg["threshold_inversion_rate"][0] > 0.2


def test_run_challenge_is_deterministic():
    a = ch.run_challenge(n_docs=40, num_resamples=100, seed=7)
    b = ch.run_challenge(n_docs=40, num_resamples=100, seed=7)
    assert a["aggregate"]["embed_tamper_detect"] == \
        b["aggregate"]["embed_tamper_detect"]
    assert a["embedding_theta"] == b["embedding_theta"]
