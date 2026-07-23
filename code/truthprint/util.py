"""Bit/byte helpers shared across Truthprint modules."""
from __future__ import annotations

__all__ = ["bits_to_bytes", "bytes_to_bits", "bits_to_str", "str_to_bits"]


def bits_to_bytes(bits: list[int]) -> bytes:
    """Pack a list of 0/1 ints into bytes (MSB-first, zero-padded)."""
    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i + 8]
        b = 0
        for bit in chunk:
            b = (b << 1) | (bit & 1)
        b <<= (8 - len(chunk))
        out.append(b)
    return bytes(out)


def bytes_to_bits(data: bytes) -> list[int]:
    """Unpack bytes into a list of 0/1 ints (MSB-first)."""
    bits: list[int] = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_to_str(bits: list[int]) -> str:
    return "".join(str(b & 1) for b in bits)


def str_to_bits(s: str) -> list[int]:
    return [1 if ch == "1" else 0 for ch in s.strip()]
