"""A real embedding-space SemStamp baseline (review W3 / Task 2).

SemStamp (Hou et al., NAACL 2024) watermarks by partitioning *sentence-embedding*
space with locality-sensitive hashing (LSH) and rejection-sampling each generated
sentence into a keyed "valid" region; detection counts how many sentences fall in
the keyed region and applies a z-test. Its carrier is therefore an embedding
*region*, not a typed invariant.

This module implements a faithful, self-contained SemStamp detector on a *real*
multilingual sentence embedding (:mod:`truthprint.embedding`). Because we compare
robustness on already-translated text (we do not re-run a generator), we grant
SemStamp the ideal generation side: each source sentence is assumed placed
exactly in its keyed target region (perfect rejection sampling). The detector
then re-embeds the (possibly translated) sentence and checks whether its LSH
signature still matches the keyed target. This isolates the *channel*
robustness question -- does the embedding-region signal survive translation? --
and is generous to SemStamp, so any gap versus the meaning-digest scheme is a
lower bound on SemStamp's disadvantage, not a strawman.

Keying (Kerckhoffs): the LSH hyperplanes and the per-position target bits derive
from the secret key and document nonce, so the mechanism is public but the
partition is secret.
"""
from __future__ import annotations

import hashlib
import math
from typing import Sequence

from . import embedding as E

__all__ = ["SemStampDetector", "target_bits", "sentence_score", "document_z"]


def target_bits(key: bytes, nonce: bytes, sent_id: str, n_bits: int) -> list[int]:
    """Keyed target LSH signature for one sentence position.

    In real SemStamp the generator would rejection-sample a realization whose
    signature equals this. We compare the observed (translated) signature to it.
    """
    out: list[int] = []
    ctr = 0
    while len(out) < n_bits:
        h = hashlib.sha256(b"semstamp|" + key + b"|" + nonce + b"|"
                           + sent_id.encode("utf-8") + b"|" + str(ctr).encode())
        for byte in h.digest():
            for b in range(8):
                out.append((byte >> b) & 1)
                if len(out) >= n_bits:
                    break
            if len(out) >= n_bits:
                break
        ctr += 1
    return out


class SemStampDetector:
    """Embedding-LSH SemStamp detector over a real multilingual encoder."""

    def __init__(self, key: bytes, n_bits: int = 4,
                 model_name: str = E.DEFAULT_MODEL):
        self.key = key
        self.n_bits = n_bits
        self.model_name = model_name
        dim = len(E.embed(["probe"], model_name)[0])
        self.planes = E.keyed_hyperplanes(key, dim, n_bits)

    def signature(self, text: str) -> list[int]:
        vec = E.embed([text], self.model_name)[0]
        return E.simhash_bits(vec, self.planes)

    def signatures(self, texts: Sequence[str]) -> list[list[int]]:
        vecs = E.embed(list(texts), self.model_name)
        return [E.simhash_bits(v, self.planes) for v in vecs]

    def doc_match_rate(self, sigs: Sequence[Sequence[int]], nonce: bytes,
                       sent_ids: Sequence[str]) -> tuple[int, int]:
        """Return (matching_bits, total_bits) of observed vs keyed targets.

        Under the (ideal) watermark the source matched all bits; after the
        channel some bits flip. Under the null (unrelated text) the match rate is
        ~1/2.
        """
        match = 0
        total = 0
        for sig, sid in zip(sigs, sent_ids):
            tgt = target_bits(self.key, nonce, sid, self.n_bits)
            match += sum(1 for a, b in zip(sig, tgt) if a == b)
            total += self.n_bits
        return match, total


def sentence_score(match: int, total: int) -> float:
    """z-score of the keyed-bit match count under the null p=1/2."""
    if total == 0:
        return 0.0
    return (match - 0.5 * total) / math.sqrt(0.25 * total)


def document_z(matches: Sequence[int], totals: Sequence[int]) -> float:
    """Document-level z aggregated over its sentences' keyed bits."""
    m = sum(matches)
    t = sum(totals)
    return sentence_score(m, t)
