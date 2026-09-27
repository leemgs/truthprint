"""SeparatedPipeline enforces distinct translate/extract models (W5 / Task 1)."""
import pytest

from truthprint.neural_parser import (NeuralInvariantExtractor, StubBackend,
                                      SeparatedPipeline)


def _extractor():
    # canned extraction reply keyed on a sentence substring
    reply = ('{"polarity":"negative","predicate":"FIX","agent":"the developer"}')
    return NeuralInvariantExtractor(StubBackend({"server": reply}))


def test_rejects_same_model():
    with pytest.raises(ValueError):
        SeparatedPipeline(lambda t, l: t, "model-X", _extractor(), "model-X")


def test_runs_with_distinct_models():
    def translate(text, lang):
        return "translated: the developer did not fix the server error"
    pipe = SeparatedPipeline(translate, "mt-model", _extractor(), "extract-model")
    out = pipe.run("source sentence", "ko")
    assert out["translate_model"] == "mt-model"
    assert out["extract_model"] == "extract-model"
    assert out["fields"]["polarity"] == "negative"
    assert out["translated"].startswith("translated:")
