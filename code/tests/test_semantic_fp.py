"""Tests for the semantic-collision false-positive floor measurement."""
import math

from truthprint.semantic_fp import (DOMAIN_CARDINALITY, measure, space_size,
                                    crossover)
from truthprint.provenance import CONTRACTS


def test_space_size_matches_cardinalities():
    for name, fields in CONTRACTS.items():
        expected = 1
        for f in fields:
            expected *= DOMAIN_CARDINALITY[f]
        assert space_size(fields) == expected
    # core6 = polarity*quantity*time_dir*attribution*predicate*agent
    assert space_size(CONTRACTS["core6"]) == 2 * 4 * 2 * 3 * 1 * 4  # 192


def test_collision_floor_dominates_crypto_bound():
    r = measure(n_facts=800, seed=7)
    core = r["contracts"]["core6"]
    # Empirical collision is close to the uniform 1/192 floor for this
    # uniform closed-domain corpus.
    assert abs(core["collision_prob"] - 1.0 / 192) < 1e-3
    # And it dwarfs the cryptographic 2^-tau bound by many orders of magnitude,
    # which is the whole point: FP is set by contract entropy, not tau.
    assert core["collision_prob"] > 1e5 * r["crypto_floor"]


def test_wider_contract_lowers_floor():
    r = measure(n_facts=800, seed=7)
    c6 = r["contracts"]["core6"]["collision_prob"]
    c9 = r["contracts"]["full9"]["collision_prob"]
    assert c9 < c6  # more fields -> more entropy -> smaller collision floor


def test_entropy_bounds():
    r = measure(n_facts=800, seed=7)
    for c in r["contracts"].values():
        # Renyi-2 (collision) entropy <= Shannon entropy <= max entropy.
        assert c["collision_entropy_bits"] <= c["shannon_entropy_bits"] + 1e-9


def test_crossover_threshold_vocab():
    cx = crossover(tau_bits=32)
    f9 = cx["contracts"]["full9"]
    c6 = cx["contracts"]["core6"]
    # full9 has two entity fields, core6 one -> full9 reaches the crypto regime
    # at a far smaller per-role vocabulary.
    assert f9["n_entity_fields"] == 2 and c6["n_entity_fields"] == 1
    assert f9["threshold_entity_vocab"] < c6["threshold_entity_vocab"]
    # full9 crosses tau at a realistic vocabulary (thousands), core6 only at a
    # practically unreachable one (tens of millions).
    assert 1e3 < f9["threshold_entity_vocab"] < 1e4
    assert c6["threshold_entity_vocab"] > 1e7
    # the threshold is exactly where contract entropy equals tau
    for c in cx["contracts"].values():
        v = c["threshold_entity_vocab"]
        h = c["nonentity_bits"] + c["n_entity_fields"] * math.log2(v)
        assert abs(h - cx["tau_bits"]) < 1e-6


def test_crossover_floor_matches_entropy():
    cx = crossover(tau_bits=32)
    for c in cx["contracts"].values():
        for row in c["rows"]:
            assert abs(row["uniform_floor"]
                       - 2.0 ** (-row["contract_entropy_bits"])) < 1e-18
            assert row["crypto_binds"] == (row["contract_entropy_bits"] > 32)
