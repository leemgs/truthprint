"""Tests for the neural-frontend adaptive-defense eval (reviewer item ①).

Scored from the committed neural-extraction cache (no API key, no network), so CI
reproduces the qualitative result deterministically: a wide-coverage neural
frontend defends the held-out (open-vocabulary) adaptive attack that the fixed
extended lexicon cannot, while preserving benign authentication and tamper
rejection.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT.parent / "paper" / "results" / "neural_defense_cache.jsonl"


def _load():
    spec = importlib.util.spec_from_file_location(
        "eval_neural_defense", ROOT / "scripts" / "eval_neural_defense.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.skipif(not CACHE.exists(), reason="neural cache not present")
def test_neural_defends_heldout_where_lexicon_cannot():
    mod = _load()
    # first 10 items reuse the committed cache (same seed/corpus prefix)
    res = mod.evaluate(n=10, seed=20270401, use_cache_only=True)
    fe = res["frontends"]
    # closed lexicon is broken by the adaptive attack
    assert fe["closed"]["adaptive_seen_valid_removal"][0] >= 0.9
    # extended lexicon defends SEEN synonyms but not the held-out novel ones
    assert fe["extended"]["adaptive_seen_valid_removal"][0] <= 0.05
    assert fe["extended"]["held_out_novel_valid_removal"][0] >= 0.9
    # neural frontend defends BOTH (open vocabulary): held-out novel removal is
    # far below the fixed lexicon's, and benign auth + tamper rejection hold
    assert (fe["neural"]["held_out_novel_valid_removal"][0]
            < fe["extended"]["held_out_novel_valid_removal"][0] - 0.3)
    assert fe["neural"]["benign_tpr"][0] >= 0.9
    assert fe["neural"]["tamper_rejection"][0] >= 0.95


@pytest.mark.skipif(not CACHE.exists(), reason="neural cache not present")
def test_cache_scoring_is_deterministic():
    mod = _load()
    a = mod.evaluate(n=10, seed=20270401, use_cache_only=True)
    b = mod.evaluate(n=10, seed=20270401, use_cache_only=True)
    assert a["frontends"] == b["frontends"]
