"""Real multilingual sentence embedding backend (optional dependency).

The stdlib-only core of Truthprint deliberately avoids models. The *baselines*
we compare against in the ACL major revision -- an embedding-space SemStamp
watermark (:mod:`truthprint.semstamp`) and embedding SimHash robust-hashing
(:mod:`truthprint.robusthash`) -- and the translator-separated neural invariant
frontend (:mod:`truthprint.neural_embed_parser`) need a *real* multilingual
sentence encoder. This module wraps one.

Design choices that keep the artifact honest and reproducible:

  * **Real, not a proxy.** We use a distilled static sentence embedding
    (``model2vec``; default ``minishlab/potion-multilingual-128M``). It is a
    genuine multilingual encoder (cross-lingual cosine >> unrelated cosine), yet
    needs no GPU and no ``torch``, so the comparison runs in this environment
    rather than only on the GPU handoff.
  * **Optional.** ``model2vec`` is an *extra*, not a core dependency. If it is
    missing the import raises a clear ``EmbeddingUnavailable`` and every script
    and test that needs it skips gracefully, so the stdlib-only core, its tests,
    and CI are unaffected.
  * **Deterministic.** The encoder is static (no sampling); the keyed LSH
    hyperplanes are drawn from a seeded PRNG derived from the secret key, so
    every reported number reproduces from a fixed seed.

Nothing here is imported by the core package; only the baseline scripts/modules
import it.
"""
from __future__ import annotations

import hashlib
import math
from functools import lru_cache
from typing import Sequence

__all__ = [
    "EmbeddingUnavailable", "available", "get_model", "embed",
    "cosine", "keyed_hyperplanes", "simhash_bits", "hamming",
    "DEFAULT_MODEL",
]

DEFAULT_MODEL = "minishlab/potion-multilingual-128M"


class EmbeddingUnavailable(RuntimeError):
    """Raised when the optional embedding backend cannot be loaded."""


def available(model_name: str = DEFAULT_MODEL) -> bool:
    """True iff the embedding backend can be loaded (import + weights present)."""
    try:
        get_model(model_name)
        return True
    except Exception:
        return False


@lru_cache(maxsize=2)
def get_model(model_name: str = DEFAULT_MODEL):
    """Load and cache the static multilingual encoder.

    Raises :class:`EmbeddingUnavailable` (never a bare ImportError) so callers
    can uniformly skip when the optional backend or its weights are absent.
    """
    try:
        from model2vec import StaticModel  # type: ignore
    except Exception as e:  # pragma: no cover - environment dependent
        raise EmbeddingUnavailable(
            "model2vec is not installed. Install the optional baseline extra: "
            "`pip install model2vec`."
        ) from e
    try:
        return StaticModel.from_pretrained(model_name)
    except Exception as e:  # pragma: no cover - network/weights dependent
        raise EmbeddingUnavailable(
            f"could not load embedding model {model_name!r}: {e}"
        ) from e


def embed(texts: Sequence[str], model_name: str = DEFAULT_MODEL) -> list[list[float]]:
    """Encode ``texts`` into unit-length embedding vectors (plain Python lists)."""
    model = get_model(model_name)
    vecs = model.encode(list(texts))
    out: list[list[float]] = []
    for v in vecs:
        v = [float(x) for x in v]
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        out.append([x / n for x in v])
    return out


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


def keyed_hyperplanes(key: bytes, dim: int, n_planes: int) -> list[list[float]]:
    """Deterministic Gaussian random hyperplanes seeded from ``key``.

    Each plane is a ``dim``-vector; their signs define an LSH bucket. Drawn from
    a key-seeded PRNG so the partition is secret and reproducible (Kerckhoffs:
    the mechanism is public, the planes depend on the key).
    """
    import random as _random

    seed = int.from_bytes(hashlib.sha256(b"tp-lsh|" + key).digest()[:8], "big")
    rng = _random.Random(seed)
    planes: list[list[float]] = []
    for _ in range(n_planes):
        # Box-Muller Gaussians for an isotropic hyperplane normal.
        plane = []
        for _ in range(dim):
            u1 = max(rng.random(), 1e-12)
            u2 = rng.random()
            plane.append(math.sqrt(-2.0 * math.log(u1)) * math.cos(2 * math.pi * u2))
        planes.append(plane)
    return planes


def simhash_bits(vec: Sequence[float], planes: Sequence[Sequence[float]]) -> list[int]:
    """Sign bits of ``vec`` against each hyperplane (the LSH signature)."""
    bits = []
    for p in planes:
        dot = sum(x * y for x, y in zip(vec, p))
        bits.append(1 if dot >= 0.0 else 0)
    return bits


def hamming(a: Sequence[int], b: Sequence[int]) -> int:
    """Hamming distance between two equal-length bit lists."""
    return sum(1 for x, y in zip(a, b) if x != y)
