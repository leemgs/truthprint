"""Secret-keyed, invariant-bound carrier map for binary carriers.

For carrier j the keyed offset is pi_j = LSB(HMAC_K(h_I || nonce || id_j)).
A code symbol c_j is realized as option a*_j = pi_j XOR c_j, and recovered as
c_j = pi_j XOR a_obs. Because pi_j depends on (K, h_I, nonce, id_j), there is
no global "option 1 means bit 1" rule an attacker could exploit.
"""
from __future__ import annotations

import hashlib
import hmac

__all__ = ["keyed_bit", "realize_option", "recover_symbol"]


def keyed_bit(key: bytes, h_I: bytes, nonce: bytes, carrier_id: int) -> int:
    msg = h_I + nonce + int(carrier_id).to_bytes(4, "big")
    return hmac.new(key, msg, hashlib.sha256).digest()[0] & 1


def realize_option(key: bytes, h_I: bytes, nonce: bytes, carrier_id: int,
                   symbol_bit: int) -> int:
    return keyed_bit(key, h_I, nonce, carrier_id) ^ (symbol_bit & 1)


def recover_symbol(key: bytes, h_I: bytes, nonce: bytes, carrier_id: int,
                   observed_option: int) -> int:
    return keyed_bit(key, h_I, nonce, carrier_id) ^ (observed_option & 1)
