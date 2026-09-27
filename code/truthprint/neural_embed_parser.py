"""Translator-independent embedding frontend for the invariant contract (Task 1).

Review W5 asked for a *wide-coverage* neural invariant extractor and, in the
follow-up, for the translation and extraction stages to use **separate models**
so the neural pilot's numbers are not confounded by one model both translating
and reading its own output (self-consistency). This module is one honest, fully
in-repo piece of that answer: a frontend that is *independent of whatever
produced the translation* because it uses a real multilingual sentence embedding
(:mod:`truthprint.embedding`), not the translating LLM.

It classifies the *categorical* invariant fields (polarity, temporal direction,
modality, causation, attribution) by nearest keyed-free English prototype in the
shared multilingual embedding space; numeric and open-string fields (quantity,
agent, patient, predicate) are abstained (``None``), never guessed, exactly like
the lexicon extractor.

What it establishes and what it does not:

  * It is genuinely **model-separated** from the translator and needs no training,
    so its measured accuracy on cached real translations is an unconfounded
    datapoint.
  * On open-domain wording it recovers *temporal direction* where the closed
    lexicon abstains (see ``scripts/eval_separated_frontend.py``), i.e. a
    translator-independent semantic frontend can read fields the lexicon cannot.
  * A *static* embedding is nonetheless insufficient for the full typed contract
    (polarity/modality/causation are near chance): whole-sentence static vectors
    encode topic more than a single logical field. This quantitatively motivates
    the instruction-LLM frontend, which is run through the separated-backend GPU
    harness (``handoff/``) as all neural/NLLB numbers in this repo are.

The extractor exposes the same ``extract(text, lang) -> dict`` interface as the
lexicon and LLM frontends, so downstream provenance/authentication is
backend-agnostic.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from .multilingual import FIELDS

__all__ = ["CATEGORICAL", "PROTOTYPES", "NeuralEmbedExtractor", "extract"]

# Fields this static-embedding frontend attempts; the rest are abstained.
CATEGORICAL = ["polarity", "time_dir", "modality", "causation", "attribution"]

# Keyed-free English class prototypes. Multilingual embeddings map a translated
# sentence near the English prototype of its class; several prototypes per class
# widen coverage. Deliberately generic (not tuned to the closed template).
PROTOTYPES: dict[str, dict[str, list[str]]] = {
    "polarity": {
        "positive": ["The team fixed the problem.", "The action was carried out.",
                     "It was done successfully.", "They completed it."],
        "negative": ["The team did not fix the problem.",
                     "The action was not carried out.", "It was never done.",
                     "They failed to complete it.", "Nothing happened."],
    },
    "time_dir": {
        "previous": ["It happened yesterday, on the previous day, last week, "
                     "last quarter, in the past."],
        "following": ["It will happen tomorrow, on the next day, next week, "
                      "in the future."],
    },
    "modality": {
        "asserted": ["It definitely happened. This is a fact. It did occur."],
        "possible": ["It may have happened. Perhaps it did. It might be. "
                     "It could occur."],
        "necessary": ["It must happen. It is required. It has to be done. "
                      "It is mandatory."],
    },
    "causation": {
        "cause": ["This happened because of that. It was caused by the outage. "
                  "Due to the failure."],
        "purpose": ["This was done in order to protect it. So as to achieve the "
                    "goal. To prevent harm."],
        "none": ["A plain statement of fact with no reason or purpose given."],
    },
    "attribution": {
        "vendor": ["According to the vendor. The vendor said. The vendor "
                   "confirmed."],
        "report": ["According to the report. Researchers reported that. "
                   "The ministry announced. Officials stated."],
        "none": ["A direct statement with no source or authority cited."],
    },
}


class NeuralEmbedExtractor:
    """Nearest-prototype categorical invariant extractor over a real encoder."""

    def __init__(self, model_name: Optional[str] = None):
        from . import embedding as E
        self.E = E
        self.model_name = model_name or E.DEFAULT_MODEL
        # Precompute prototype embeddings once.
        self._proto = {}
        for field, classes in PROTOTYPES.items():
            self._proto[field] = {
                cls: E.embed(texts, self.model_name)
                for cls, texts in classes.items()
            }

    def _classify(self, vec, field: str) -> Optional[str]:
        best_score = None
        best_cls = None
        for cls, protos in self._proto[field].items():
            score = max(self.E.cosine(vec, p) for p in protos)
            if best_score is None or score > best_score:
                best_score = score
                best_cls = cls
        return best_cls

    def extract(self, text: str, lang: str = "en") -> dict:
        vec = self.E.embed([text], self.model_name)[0]
        out = {f: None for f in FIELDS}
        for field in CATEGORICAL:
            out[field] = self._classify(vec, field)
        return out


@lru_cache(maxsize=1)
def _default_extractor():
    return NeuralEmbedExtractor()


def extract(text: str, lang: str = "en") -> dict:
    """Module-level convenience wrapper (lazy, cached)."""
    return _default_extractor().extract(text, lang)
