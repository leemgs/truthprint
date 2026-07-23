"""Authenticated payload: p = m || truncate(HMAC_K(m || n || h_I), tau).

Attribution requires a valid MAC tag, so forging attribution reduces to
forging the MAC (Theorem 1 in the paper), and the false-positive rate of the
authenticated channel is bounded by 2^-tau (Theorem 2).
"""
from __future__ import annotations

import hashlib
import hmac

from .util import bits_to_bytes, bytes_to_bits

__all__ = ["authenticate_payload", "verify_payload", "tag_bits_of"]


def _tag(key: bytes, msg_bits: list[int], nonce: bytes, h_I: bytes,
         tag_bits: int) -> list[int]:
    mac = hmac.new(key, bits_to_bytes(msg_bits) + nonce + h_I,
                   hashlib.sha256).digest()
    return bytes_to_bits(mac)[:tag_bits]


def authenticate_payload(key: bytes, msg_bits: list[int], nonce: bytes,
                         h_I: bytes, tag_bits: int) -> list[int]:
    """Return the payload bits p = m || tag."""
    return list(msg_bits) + _tag(key, msg_bits, nonce, h_I, tag_bits)


def verify_payload(key: bytes, payload_bits: list[int], nonce: bytes,
                   h_I: bytes, msg_len: int, tag_bits: int) -> bool:
    """Constant-time verification of a recovered payload."""
    msg_bits = payload_bits[:msg_len]
    recv_tag = payload_bits[msg_len:msg_len + tag_bits]
    exp_tag = _tag(key, msg_bits, nonce, h_I, tag_bits)
    return hmac.compare_digest(bytes(recv_tag), bytes(exp_tag))


def tag_bits_of(msg_len: int, payload_len: int) -> int:
    return payload_len - msg_len
