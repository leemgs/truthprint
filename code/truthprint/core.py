"""High-level Truthprint codec over abstract binary carriers.

This ties together the invariant digest, authenticated payload, GF(2) code, and
keyed carrier map. It operates on *abstract* carrier options; the linguistic
layer (:mod:`truthprint.linguistic`) maps these to and from real sentences.
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass

from .invariants import canonical_digest
from .payload import authenticate_payload, verify_payload
from .coding import GF2Code
from .carriers import realize_option, recover_symbol

__all__ = ["Truthprint", "DetectionResult"]


@dataclass
class DetectionResult:
    attributed: bool           # True iff the MAC verified (authenticated)
    message: list[int] | None  # recovered message bits, or None
    z_score: float             # statistical fallback score under H0 ~ N(0,1)
    reliable_carriers: int     # non-erased carriers used
    erasures: int              # erased carriers
    decoded: bool              # whether ECC produced a candidate payload


class Truthprint:
    """Reference codec.

    Parameters mirror the paper's reference configuration. ``code_n`` is the
    number of binary carriers; the payload has ``msg_len + tag_bits`` bits and
    the code rate is ``(msg_len + tag_bits) / code_n``.
    """

    def __init__(self, key: bytes, msg_len: int = 16, tag_bits: int = 32,
                 code_n: int = 96, code_seed: int = 0xC0FFEE):
        self.key = key
        self.msg_len = msg_len
        self.tag_bits = tag_bits
        self.k = msg_len + tag_bits
        self.code = GF2Code(self.k, code_n, code_seed)
        self.n_carriers = code_n

    # -- convenience ------------------------------------------------------
    @staticmethod
    def new_nonce(size: int = 12) -> bytes:
        return os.urandom(size)

    def min_reliable_carriers(self) -> int:
        """Carriers that must survive for high-probability recovery (= k)."""
        return self.k

    # -- encode / detect --------------------------------------------------
    def encode(self, invariants: dict, msg_bits: list[int],
               nonce: bytes) -> list[int]:
        """Return realized carrier options (one per carrier)."""
        if len(msg_bits) != self.msg_len:
            raise ValueError(f"msg_bits must have length {self.msg_len}")
        h_I = canonical_digest(invariants)
        p = authenticate_payload(self.key, msg_bits, nonce, h_I, self.tag_bits)
        c = self.code.encode(p)
        return [realize_option(self.key, h_I, nonce, j, c[j])
                for j in range(self.n_carriers)]

    def detect(self, invariants: dict, observed_options: list[int],
               nonce: bytes,
               erasure_mask: list[bool] | None = None) -> DetectionResult:
        """Attempt authenticated attribution from observed carrier options.

        ``erasure_mask[j] = True`` marks carrier j as destroyed/unreliable.
        """
        h_I = canonical_digest(invariants)  # re-derived by the detector
        received: list[int | None] = []
        recovered_syms: list[int | None] = []
        for j in range(self.n_carriers):
            if erasure_mask is not None and erasure_mask[j]:
                received.append(None)
                recovered_syms.append(None)
            else:
                s = recover_symbol(self.key, h_I, nonce, j, observed_options[j])
                received.append(s)
                recovered_syms.append(s)

        erasures = sum(1 for r in received if r is None)
        reliable = self.n_carriers - erasures

        p_hat = self.code.decode_erasure(received)
        attributed = False
        message = None
        z = 0.0
        if p_hat is not None:
            attributed = verify_payload(self.key, p_hat, nonce, h_I,
                                        self.msg_len, self.tag_bits)
            if attributed:
                message = p_hat[:self.msg_len]
            # statistical fallback: agreement between observed carriers and the
            # re-encoded candidate codeword (under H0 ~ Binomial(reliable, 1/2))
            c_hat = self.code.encode(p_hat)
            matches = sum(1 for j in range(self.n_carriers)
                          if recovered_syms[j] is not None
                          and recovered_syms[j] == c_hat[j])
            if reliable > 0:
                z = (matches - 0.5 * reliable) / math.sqrt(0.25 * reliable)
        return DetectionResult(attributed=attributed, message=message,
                               z_score=z, reliable_carriers=reliable,
                               erasures=erasures, decoded=p_hat is not None)
