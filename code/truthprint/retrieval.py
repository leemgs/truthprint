"""Ledger-based retrieval (+NLI) baseline --- the "just store the source" control.

A reviewer's sharpest question about the surviving *meaning-digest* scheme is that
it already needs an out-of-band ledger, so why not simply **store the source in
that ledger and retrieve it** after transformation (nearest-neighbor over a
sentence embedding), optionally checking entailment (NLI) to reject edits? This
module implements exactly that baseline so the comparison is head-to-head under
the *same* ledger assumption as :mod:`truthprint.provenance`.

Components:
  * :class:`LedgerRetriever` -- registers a gallery of source representations and
    attributes a (possibly transformed) candidate to its nearest gallery entry by
    cosine. Backend is pluggable: a transparent bag-of-words vector by default
    (stdlib, deterministic, runs in CI), or a real multilingual sentence embedding
    (:mod:`truthprint.embedding`, ``model2vec``) when available.
  * Verification variants layered on retrieval:
      - ``retrieval``          : attribute iff nearest-neighbor cosine >= threshold
                                 (no meaning check).
      - ``retrieval+nli_proxy``: after retrieval, a cheap deterministic entailment
                                 proxy (bidirectional lexical overlap, calibrated to
                                 keep legitimate paraphrases) must also pass.
      - ``retrieval+nli_oracle``: an *unrealizable ceiling* -- accept iff the
                                 candidate truly preserves the source's typed
                                 contract (gold invariants). This is the behavior a
                                 *perfect* NLI model would give.

The decisive contrast (measured in ``scripts/eval_retrieval.py``): retrieval
attributes a transformed sentence back to its source across paraphrase, but a
single-field meaning-altering edit stays nearest to that same source, so
retrieval *cannot reject the tamper* and a cheap NLI proxy barely helps; only a
perfect (oracle) NLI matches the typed contract's tamper rejection --- and even
then it neither *localizes which field changed* nor gives a *keyed, unforgeable*
tag, which the typed meaning-digest does deterministically with no model.
"""
from __future__ import annotations

import math
from typing import Callable, Optional

from .challenge import cosine_bow, _bow

__all__ = [
    "LedgerRetriever", "nli_proxy_entail", "source_coverage",
    "contract_preserved", "bow_embed", "bow_cosine",
]


# --- default transparent backend: bag-of-words vectors -------------------- #
def bow_embed(text: str) -> dict:
    """A transparent bag-of-words 'embedding' (token -> count). Stdlib-only."""
    return _bow(text)


def bow_cosine(a: dict, b: dict) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values())) or 1.0
    nb = math.sqrt(sum(v * v for v in b.values())) or 1.0
    return dot / (na * nb)


class LedgerRetriever:
    """Nearest-neighbor attributor over a stored gallery of source reps.

    ``embed`` maps text to a vector; ``cosine`` scores two vectors. Defaults use a
    bag-of-words vector so the baseline runs anywhere; pass the real embedding
    backend (:func:`truthprint.embedding.embed`/``cosine``) for a strong encoder.
    """

    def __init__(self, embed: Optional[Callable] = None,
                 cosine: Optional[Callable] = None):
        self.embed = embed or bow_embed
        self.cosine = cosine or bow_cosine
        self._ids: list[str] = []
        self._vecs: list = []

    def build(self, gallery: dict) -> "LedgerRetriever":
        """Register the ledger: ``{sent_id: source_text}``."""
        self._ids = list(gallery.keys())
        self._vecs = [self.embed(gallery[sid]) for sid in self._ids]
        return self

    def attribute(self, text: str):
        """Return ``(best_sent_id, cosine)`` for the nearest gallery entry."""
        if not self._ids:
            return None, 0.0
        q = self.embed(text)
        best_i, best_s = 0, -1.0
        for i, v in enumerate(self._vecs):
            s = self.cosine(q, v)
            if s > best_s:
                best_i, best_s = i, s
        return self._ids[best_i], best_s


def source_coverage(source_text: str, candidate_text: str) -> float:
    """Directional token coverage: fraction of the source's content tokens that
    also appear in the candidate. A crude *entailment* signal (does the candidate
    still contain what the source asserts) distinct from symmetric cosine."""
    src = _bow(source_text)
    cand = set(_bow(candidate_text))
    if not src:
        return 1.0
    return sum(1 for t in src if t in cand) / len(src)


def nli_proxy_entail(source_text: str, candidate_text: str,
                     theta: float) -> bool:
    """A cheap, deterministic 'entailment' proxy: directional token coverage
    (:func:`source_coverage`) at least ``theta``. Stands in for a lightweight NLI
    gate an engineer would actually deploy. It catches edits that drop a source
    token but is blind to typed changes that keep the tokens (and cannot say
    *which* field changed), as the eval measures."""
    return source_coverage(source_text, candidate_text) >= theta


def contract_preserved(gold_source: dict, gold_candidate: dict,
                       fields: list[str]) -> bool:
    """Oracle NLI ceiling: True iff the candidate truly preserves the source's
    typed contract (ground-truth invariants). This is what a *perfect* NLI model
    would return; it is unrealizable at deploy time and, unlike the typed digest,
    does not localize the changed field or yield a keyed tag."""
    return all(gold_source.get(k) == gold_candidate.get(k) for k in fields)
