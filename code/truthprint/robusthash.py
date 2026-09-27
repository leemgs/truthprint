"""Robust-hashing provenance baselines (review W2 / Task 3).

A natural question about the meaning-digest scheme is: how is registering a keyed
tag over an invariant *contract* in a ledger different from classic *robust
hashing* -- registering a similarity-preserving fingerprint of the content and
looking it up after transformation? This module implements the standard
robust-hashing family so the paper can position (and measure) the difference
rather than assert it:

  * **exact hash** -- SHA-256 of the surface text (cryptographic fingerprint;
    the ``git``/dedup baseline);
  * **token MinHash / Jaccard** -- shingle-set similarity (near-duplicate
    detection, e.g. broadcast monitoring);
  * **embedding SimHash** -- sign bits of a real multilingual sentence embedding
    (semantic/perceptual hashing).

Each is turned into a provenance verifier: register a fingerprint of the source,
then verify a (possibly translated) sentence by fingerprint proximity. The point
the comparison makes: robust hashing answers *"is this the same string / the same
tokens / a nearby point in embedding space?"*, none of which is *"is the typed
meaning -- polarity, quantity, time, attribution -- preserved?"*. Surface and
token hashes die under translation; the embedding hash drifts across languages
(measured in :mod:`truthprint.semstamp`) and, crucially, carries **no typed
tamper localization**: a single-field meaning-altering edit can leave the
fingerprint inside tolerance, exactly the failure the challenge set (C3) shows for
a similarity gate. The meaning-digest scheme instead verifies a keyed tag over
typed invariants, so it both survives translation and rejects a single-field
tamper.
"""
from __future__ import annotations

import hashlib
from typing import Sequence

__all__ = [
    "sha256_hex", "shingles", "minhash_signature", "minhash_similarity",
    "jaccard", "simhash_from_vec", "simhash_match",
    "exact_verify", "minhash_verify",
]


def sha256_hex(text: str) -> str:
    """Exact cryptographic fingerprint of the (normalized) surface text."""
    norm = " ".join(text.strip().split()).lower()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def exact_verify(source_text: str, observed_text: str) -> bool:
    """Robust-hash verify with an *exact* hash: matches iff surface is identical."""
    return sha256_hex(source_text) == sha256_hex(observed_text)


def shingles(text: str, k: int = 3) -> set[str]:
    """Character k-shingles (language-agnostic near-duplicate features)."""
    s = " ".join(text.strip().split()).lower()
    if len(s) < k:
        return {s} if s else set()
    return {s[i:i + k] for i in range(len(s) - k + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def minhash_signature(text: str, num_perm: int = 64, k: int = 3) -> list[int]:
    """MinHash signature of the shingle set (near-duplicate fingerprint)."""
    sh = shingles(text, k)
    sig: list[int] = []
    for i in range(num_perm):
        salt = str(i).encode()
        best = None
        for token in sh:
            h = int.from_bytes(
                hashlib.blake2b(token.encode("utf-8"), salt=salt[:8].ljust(8, b"0"),
                                digest_size=8).digest(), "big")
            if best is None or h < best:
                best = h
        sig.append(best if best is not None else 0)
    return sig


def minhash_similarity(sig_a: Sequence[int], sig_b: Sequence[int]) -> float:
    """Estimated Jaccard similarity from two MinHash signatures."""
    if not sig_a or not sig_b:
        return 0.0
    same = sum(1 for x, y in zip(sig_a, sig_b) if x == y)
    return same / len(sig_a)


def minhash_verify(source_text: str, observed_text: str, threshold: float = 0.5,
                   num_perm: int = 64, k: int = 3) -> bool:
    """Robust-hash verify with MinHash: matches iff shingle similarity >= threshold."""
    a = minhash_signature(source_text, num_perm, k)
    b = minhash_signature(observed_text, num_perm, k)
    return minhash_similarity(a, b) >= threshold


def simhash_from_vec(vec: Sequence[float], planes: Sequence[Sequence[float]]) -> list[int]:
    """SimHash sign bits of an embedding vector against random hyperplanes."""
    from .embedding import simhash_bits
    return simhash_bits(vec, planes)


def simhash_match(bits_a: Sequence[int], bits_b: Sequence[int],
                  max_hamming: int) -> bool:
    """Embedding SimHash verify: matches iff Hamming distance <= max_hamming."""
    from .embedding import hamming
    return hamming(bits_a, bits_b) <= max_hamming
