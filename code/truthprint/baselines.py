"""Reference baselines for the paper's comparison tables (Sec. Evaluation).

Small, self-contained, standard-library-only implementations of the *detection
statistics* of four published watermarks, so their behaviour can be measured on
the same closed-domain Stage-1 testbed used for Truthprint
(see :mod:`truthprint.linguistic`). Each baseline is a faithful reduction of
*where the published method places its signal* and *how it scores detection*;
it abstracts the neural frontend (LM sampling, sentence encoder, AMR parser)
exactly as the Truthprint Stage-1 numbers do.

    SynthID-Text / KGW  -- token-level green-list   (signal in token identity)
    DEW                 -- distortion-free, edit-aligned token watermark
    SemStamp            -- sentence-embedding LSH region (signal in embedding)
    SWAN                -- AMR / semantic-structure slots (signal in meaning)

Shared channel model
--------------------
A single meaning-preserving transform (paraphrase/translation) is characterised
by two *physical* quantities every method sees identically:

    tau_tok : fraction of surface tokens replaced by the transform. A
              cross-script translation replaces almost all tokens; a light
              paraphrase replaces few.
    eps_inv : fraction of meaning-layer carriers lost to parse normalisation --
              the quantity Truthprint's own Table VI already uses.

Each method's survival is *derived* from these two numbers through its own
signal dependence, so the relative ordering is forced by signal placement,
not chosen per method:

    KGW      green bit keyed by the (prev, tok) bigram   -> survival ~ (1-tau)^2
    DEW      bit keyed by the token alone, edit-aligned   -> survival ~ (1-tau),
             with a hard alignment cliff past an edit budget B
    SemStamp region bit = sign(w_m*meaning + w_s*surface) -> flips w.p.
             ~0.5*w_s*tau near the LSH boundary (meaning-dominant => robust)
    SWAN     structural slot at the meaning layer          -> unaffected by tau;
             lost only when the meaning carrier is erased (eps_inv)

Every class exposes ``embed(doc, key)`` and ``score(doc, key)``; ``score``
returns a z-like statistic, large under a true watermark and ~N(0,1) under the
null, suitable for ROC-AUC / TPR@FPR.
"""
from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field

__all__ = [
    "Sentence", "Document", "make_document", "channel",
    "KGWGreenList", "DEWEditRobust", "SemStampLSH", "SWANStructural",
]


# --------------------------------------------------------------------------- #
# Shared document model
# --------------------------------------------------------------------------- #
@dataclass
class Sentence:
    """One sentence: a locked meaning plus a mutable surface token stream.

    ``region_bit`` and ``struct_bit`` carry the sentence-level and meaning-level
    watermark bits set by SemStamp / SWAN at embed time; ``None`` in a null
    (un-watermarked) sentence, where they are treated as random at scoring.
    """
    meaning: int
    tokens: list[int]
    region_bit: int | None = None   # SemStamp LSH region bit
    struct_bit: int | None = None   # SWAN structural slot bit
    meaning_erased: bool = False    # set by the channel: meaning carrier lost


@dataclass
class Document:
    sentences: list[Sentence] = field(default_factory=list)


def _h(*parts) -> int:
    m = hashlib.sha256()
    for p in parts:
        m.update(str(p).encode())
        m.update(b"\x00")
    return int.from_bytes(m.digest()[:8], "big")


def make_document(n_sentences: int, tokens_per_sentence: int,
                  rng: random.Random) -> Document:
    """A null (un-watermarked) document with random surface tokens and bits."""
    sents = []
    for _ in range(n_sentences):
        sents.append(Sentence(
            meaning=rng.randrange(1 << 32),
            tokens=[rng.randrange(1 << 16) for _ in range(tokens_per_sentence)],
            region_bit=rng.randrange(2),
            struct_bit=rng.randrange(2),
        ))
    return Document(sents)


def channel(doc: Document, tau_tok: float, eps_inv: float,
            rng: random.Random) -> Document:
    """Apply one meaning-preserving transform.

    Replaces a ``tau_tok`` fraction of surface tokens (hurts token methods),
    flips each sentence's SemStamp region bit with probability
    ``0.5 * SemStampLSH.w_s * tau_tok`` (LSH-boundary crossing driven by the
    surface component of the embedding), preserves the SWAN structural bit
    (meaning layer) but erases it with probability ``eps_inv`` (parse failure).
    Meaning is preserved throughout.
    """
    out = []
    p_flip = 0.5 * SemStampLSH.w_s * tau_tok
    for s in doc.sentences:
        toks = [rng.randrange(1 << 16) if rng.random() < tau_tok else t
                for t in s.tokens]
        rb = s.region_bit
        if rb is not None and rng.random() < p_flip:
            rb ^= 1
        out.append(Sentence(
            meaning=s.meaning, tokens=toks,
            region_bit=rb, struct_bit=s.struct_bit,
            meaning_erased=(rng.random() < eps_inv),
        ))
    return Document(out)


def _zscore(matches: int, n: int, p0: float) -> float:
    if n == 0:
        return 0.0
    var = p0 * (1.0 - p0) * n
    if var <= 0:
        return 0.0
    return (matches - p0 * n) / math.sqrt(var)


# --------------------------------------------------------------------------- #
# 1. SynthID-Text / KGW  -- token-level green-list watermark
# --------------------------------------------------------------------------- #
class KGWGreenList:
    """Green-red list watermark (Kirchenbauer et al.); SynthID-Text shares the
    same token-identity-keyed detection statistic (tournament sampling changes
    the *sampler*, not the token-level dependence exploited here).

    Green bit of a token depends on the previous token (context seed) and the
    token itself: ``g = H(key, prev, tok) mod 2``. Watermarked text is generated
    so every token is green; the detector counts green tokens and reports the
    standard z-statistic. Because the bit is keyed by the (prev, tok) bigram,
    replacing a token randomises its own bit *and* its successor's context, so
    the statistic decays as ``(1 - tau_tok)^2``.
    """
    gamma = 0.5

    def _green(self, key: bytes, prev: int, tok: int) -> int:
        return _h(key, "kgw", prev, tok) % 2

    def embed(self, doc: Document, key: bytes) -> Document:
        out = []
        for s in doc.sentences:
            toks, prev = [], 0
            for _ in s.tokens:
                t = 0
                while self._green(key, prev, t) != 1:
                    t += 1
                toks.append(t)
                prev = t
            out.append(Sentence(meaning=s.meaning, tokens=toks))
        return Document(out)

    def score(self, doc: Document, key: bytes) -> float:
        n = green = 0
        for s in doc.sentences:
            prev = 0
            for t in s.tokens:
                green += self._green(key, prev, t)
                prev = t
                n += 1
        return _zscore(green, n, self.gamma)


# --------------------------------------------------------------------------- #
# 2. DEW  -- distortion-free, edit-robust token watermark
# --------------------------------------------------------------------------- #
class DEWEditRobust:
    """Distortion-free token watermark with edit-tolerant alignment
    (Kuditipudi et al. lineage). Each token carries a key bit keyed by the token
    alone (not the bigram), so it is more edit-robust than KGW -- survival
    ``~ (1 - tau_tok)`` rather than ``(1 - tau_tok)^2`` -- but the alignment
    fails once the edit fraction exceeds a budget ``B`` (e.g. cross-lingual
    translation), collapsing the statistic.
    """
    budget = 0.5

    def _bit(self, key: bytes, tok: int) -> int:
        return _h(key, "dew", tok) % 2

    def embed(self, doc: Document, key: bytes) -> Document:
        out = []
        for s in doc.sentences:
            toks = []
            for _ in s.tokens:
                t = 0
                while self._bit(key, t) != 1:
                    t += 1
                toks.append(t)
            out.append(Sentence(meaning=s.meaning, tokens=toks))
        return Document(out)

    def score(self, doc: Document, key: bytes) -> float:
        n = ones = 0
        for s in doc.sentences:
            for t in s.tokens:
                ones += self._bit(key, t)
                n += 1
        if n == 0:
            return 0.0
        z = _zscore(ones, n, 0.5)
        # alignment gate: estimate the edit fraction from the surviving-bit rate
        # (ones/n = 0.5 + 0.5*(1-tau)); collapse if it exceeds the edit budget.
        est_change = max(0.0, min(1.0, 2.0 * (1.0 - ones / n)))
        if est_change > self.budget:
            return 0.0
        return z


# --------------------------------------------------------------------------- #
# 3. SemStamp  -- sentence-embedding LSH-region watermark
# --------------------------------------------------------------------------- #
class SemStampLSH:
    """Semantic sentence watermark (SemStamp): embed each sentence, take an LSH
    region bit, and generate sentences whose region matches a key target. The
    region bit is meaning-dominant (``w_m > w_s``), reproducing SemStamp's
    paraphrase robustness; the surface component still flips a fraction of bits
    near the LSH boundary (handled by :func:`channel`), so it degrades under
    heavy surface change but far more gracefully than token methods. It carries
    no authentication and no ECC (Truthprint's additions).
    """
    w_m = 0.70
    w_s = 0.30

    def _target(self, key: bytes, meaning: int) -> int:
        return _h(key, "sem-t", meaning) % 2

    def embed(self, doc: Document, key: bytes) -> Document:
        # the generator lands each sentence in its target region (embed succeeds)
        return Document([
            Sentence(meaning=s.meaning, tokens=list(s.tokens),
                     region_bit=self._target(key, s.meaning))
            for s in doc.sentences
        ])

    def score(self, doc: Document, key: bytes) -> float:
        n = match = 0
        for s in doc.sentences:
            rb = s.region_bit
            if rb is None:
                rb = _h("null", s.meaning) % 2  # null sentence: random region
            if rb == self._target(key, s.meaning):
                match += 1
            n += 1
        return _zscore(match, n, 0.5)


# --------------------------------------------------------------------------- #
# 4. SWAN  -- AMR / semantic-structure watermark
# --------------------------------------------------------------------------- #
class SWANStructural:
    """Structured-semantic watermark (SWAN) embedding bits into AMR-graph slot
    choices. The signal lives at the meaning layer, so it survives surface
    token change entirely and is lost only when the meaning carrier is erased
    (``eps_inv``). Base SWAN has no MAC authentication and no erasure ECC, so
    detection is statistical only: count sentences whose recovered structural
    bit matches the key target over the surviving (non-erased) sentences.
    """
    def _target(self, key: bytes, meaning: int) -> int:
        return _h(key, "swan-t", meaning) % 2

    def embed(self, doc: Document, key: bytes) -> Document:
        return Document([
            Sentence(meaning=s.meaning, tokens=list(s.tokens),
                     struct_bit=self._target(key, s.meaning))
            for s in doc.sentences
        ])

    def score(self, doc: Document, key: bytes) -> float:
        n = match = 0
        for s in doc.sentences:
            if s.meaning_erased:
                continue  # parse failure -> no structural bit recovered
            sb = s.struct_bit
            if sb is None:
                sb = _h("null", s.meaning) % 2  # null sentence: random slot
            if sb == self._target(key, s.meaning):
                match += 1
            n += 1
        return _zscore(match, n, 0.5)
