"""Tests for the semantic-collision false-positive floor measurement."""
import math

from truthprint.semantic_fp import DOMAIN_CARDINALITY, measure, space_size
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
        assert c["shannon_entropy_bits"] <= c["max_entropy_bits"] + 1e-9
