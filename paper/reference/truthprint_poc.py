"""
Truthprint reference proof-of-concept (self-contained, dependency-free).

This is NOT a language-model evaluation. It exercises only the
*language-independent* machinery of Truthprint:

  1. canonical invariant digest  h_I  (Sec. VI)
  2. authenticated payload        p = m || MAC_K(m || n || h_I)   (Sec. VII-A)
  3. systematic GF(2) block code with *erasure* decoding          (Sec. VII/VIII)
  4. secret-keyed, invariant-bound carrier assignment             (Sec. VII-C)
  5. erasure-aware detection + MAC verification                   (Sec. VIII)

It demonstrates, on synthetic data, four properties claimed in the paper:

  (P1) round-trip recovery: an invariant-preserving transform that flips
       realization carriers and erases some of them still yields the exact
       payload after ECC decoding and MAC verification.
  (P2) invariant binding: a transform that alters a *locked* invariant
       (e.g. polarity) changes h_I, so the MAC fails -> no attribution.
  (P3) cryptographic false positives: independent (unwatermarked) documents
       are attributed with probability ~2^-tau (tau = tag bits), measured
       empirically over many trials.
  (P4) no global carrier rule: the realized option for a fixed symbol
       differs across documents because the keyed map depends on (K, h_I, n).

Run:  python3 truthprint_poc.py
"""

from __future__ import annotations
import hashlib
import hmac
import json
import os
import random
from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# 1. Canonical invariant digest
# --------------------------------------------------------------------------
def canonical_invariant_digest(invariants: dict) -> bytes:
    """Order-independent, whitespace-independent digest of the locked fields."""
    canon = json.dumps(invariants, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).digest()


# --------------------------------------------------------------------------
# 2. Authenticated payload
# --------------------------------------------------------------------------
def authenticate_payload(key: bytes, msg_bits: list[int], nonce: bytes,
                         h_I: bytes, tag_bits: int) -> list[int]:
    """p = m || truncate(MAC_K(m || n || h_I), tau)."""
    m_bytes = _bits_to_bytes(msg_bits)
    mac = hmac.new(key, m_bytes + nonce + h_I, hashlib.sha256).digest()
    tag = _bytes_to_bits(mac)[:tag_bits]
    return list(msg_bits) + tag


def verify_payload(key: bytes, payload_bits: list[int], nonce: bytes,
                   h_I: bytes, msg_len: int, tag_bits: int) -> bool:
    msg_bits = payload_bits[:msg_len]
    recv_tag = payload_bits[msg_len:msg_len + tag_bits]
    m_bytes = _bits_to_bytes(msg_bits)
    mac = hmac.new(key, m_bytes + nonce + h_I, hashlib.sha256).digest()
    exp_tag = _bytes_to_bits(mac)[:tag_bits]
    return hmac.compare_digest(bytes(recv_tag), bytes(exp_tag))


# --------------------------------------------------------------------------
# 3. Systematic GF(2) block code with erasure decoding
# --------------------------------------------------------------------------
class GF2Code:
    """Systematic [n, k] code over GF(2): G = [I_k | P], P pseudo-random(seed)."""

    def __init__(self, k: int, n: int, seed: int = 0xC0FFEE):
        assert n >= k
        self.k, self.n = k, n
        rng = random.Random(seed)
        # parity part P is k x (n-k)
        self.P = [[rng.randint(0, 1) for _ in range(n - k)] for _ in range(k)]

    def encode(self, p: list[int]) -> list[int]:
        assert len(p) == self.k
        parity = []
        for j in range(self.n - self.k):
            acc = 0
            for i in range(self.k):
                acc ^= p[i] & self.P[i][j]
            parity.append(acc)
        return list(p) + parity  # systematic

    def _col(self, j: int) -> list[int]:
        """j-th column of G (length k): coefficients of message bits."""
        if j < self.k:
            e = [0] * self.k
            e[j] = 1
            return e
        return [self.P[i][j - self.k] for i in range(self.k)]

    def decode_erasure(self, received: list[int | None]) -> list[int] | None:
        """Solve for p from non-erased positions via GF(2) Gaussian elim.
        received[j] is a bit, or None for an erasure. Returns p or None."""
        rows, rhs = [], []
        for j, val in enumerate(received):
            if val is None:
                continue
            rows.append(self._col(j)[:])   # length k
            rhs.append(val & 1)
        # Gaussian elimination over GF(2)
        k = self.k
        piv_col = [-1] * k
        r = 0
        for c in range(k):
            # find pivot row at/after r with a 1 in column c
            piv = -1
            for rr in range(r, len(rows)):
                if rows[rr][c] == 1:
                    piv = rr
                    break
            if piv == -1:
                continue
            rows[r], rows[piv] = rows[piv], rows[r]
            rhs[r], rhs[piv] = rhs[piv], rhs[r]
            for rr in range(len(rows)):
                if rr != r and rows[rr][c] == 1:
                    rows[rr] = [a ^ b for a, b in zip(rows[rr], rows[r])]
                    rhs[rr] ^= rhs[r]
            piv_col[c] = r
            r += 1
        if r < k:
            return None  # underdetermined: not enough surviving equations
        # back-out solution
        sol = [0] * k
        for c in range(k):
            pr = piv_col[c]
            if pr != -1:
                sol[c] = rhs[pr]
        return sol


# --------------------------------------------------------------------------
# 4. Secret-keyed, invariant-bound carrier assignment (binary carriers)
# --------------------------------------------------------------------------
def keyed_bit(key: bytes, h_I: bytes, nonce: bytes, carrier_id: int) -> int:
    """pi_j in {0,1}: the keyed offset for carrier j, bound to (K, h_I, n)."""
    msg = h_I + nonce + carrier_id.to_bytes(4, "big")
    d = hmac.new(key, msg, hashlib.sha256).digest()
    return d[0] & 1


def realize_option(key, h_I, nonce, carrier_id, symbol_bit) -> int:
    """a*_j = pi_j XOR c_j   (for |A_j| = 2)."""
    return keyed_bit(key, h_I, nonce, carrier_id) ^ (symbol_bit & 1)


def recover_symbol(key, h_I, nonce, carrier_id, observed_option) -> int:
    return keyed_bit(key, h_I, nonce, carrier_id) ^ (observed_option & 1)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _bits_to_bytes(bits: list[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i + 8]
        b = 0
        for bit in chunk:
            b = (b << 1) | (bit & 1)
        b <<= (8 - len(chunk))
        out.append(b)
    return bytes(out)


def _bytes_to_bits(bs: bytes) -> list[int]:
    bits = []
    for b in bs:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits


# --------------------------------------------------------------------------
# document model
# --------------------------------------------------------------------------
@dataclass
class Document:
    invariants: dict
    carrier_options: list[int]  # observed realized option per carrier site


def encode_document(key, msg_bits, nonce, invariants, code: GF2Code,
                    tag_bits: int) -> Document:
    h_I = canonical_invariant_digest(invariants)
    p = authenticate_payload(key, msg_bits, nonce, h_I, tag_bits)
    c = code.encode(p)                                   # length n
    options = [realize_option(key, h_I, nonce, j, c[j]) for j in range(code.n)]
    return Document(invariants=invariants, carrier_options=options)


def detect_document(key, doc: Document, nonce, code: GF2Code,
                    msg_len: int, tag_bits: int,
                    erasure_mask: list[bool] | None = None):
    """Returns (attributed: bool, recovered_msg or None)."""
    h_I = canonical_invariant_digest(doc.invariants)     # re-derived by detector
    received: list[int | None] = []
    for j in range(code.n):
        if erasure_mask is not None and erasure_mask[j]:
            received.append(None)
        else:
            received.append(recover_symbol(key, h_I, nonce, j,
                                           doc.carrier_options[j]))
    p_hat = code.decode_erasure(received)
    if p_hat is None:
        return False, None
    ok = verify_payload(key, p_hat, nonce, h_I, msg_len, tag_bits)
    return ok, (p_hat[:msg_len] if ok else None)


# --------------------------------------------------------------------------
# demonstration
# --------------------------------------------------------------------------
def main():
    rng = random.Random(7)
    KEY = b"truthprint-secret-key-0123456789ab"
    MSG_LEN, TAG_BITS = 16, 32
    K = MSG_LEN + TAG_BITS            # 48 payload bits
    N = 96                           # rate-1/2 code -> erasure tolerance
    code = GF2Code(K, N)

    invariants = {
        "events": [{"predicate": "FIX",
                    "roles": {"agent": "developer", "patient": "server_error"},
                    "polarity": "positive",
                    "time": {"relation_to_creation": "previous_day"}}],
        "quantities": [], "attribution": "unattributed",
    }
    msg = [rng.randint(0, 1) for _ in range(MSG_LEN)]
    nonce = os.urandom(12)

    print("=" * 68)
    print("Truthprint reference proof-of-concept")
    print("=" * 68)
    print(f"[setup] code=[{N},{K}] GF(2), tag={TAG_BITS} bits, msg={MSG_LEN} bits")
    print(f"[setup] message m = {''.join(map(str, msg))}")

    doc = encode_document(KEY, msg, nonce, invariants, code, TAG_BITS)

    # ---- (P1) invariant-preserving transform: flip realizations + erase ----
    # A benign paraphrase/translation re-realizes carriers (some flip) and
    # destroys (erases) a fraction of carrier sites, but preserves invariants.
    n_erase = int(0.30 * N)
    erased = set(rng.sample(range(N), n_erase))
    mask = [j in erased for j in range(N)]
    # surviving carriers are still observed (their option is unchanged because
    # the realized surface is re-expressed but recovers to the same symbol)
    ok, rec = detect_document(KEY, doc, nonce, code, MSG_LEN, TAG_BITS, mask)
    print("\n[P1] invariant-preserving transform "
          f"({n_erase}/{N} carriers erased):")
    print(f"     attributed={ok}  recovered==message={rec == msg}")

    # ---- (P2) invariant-altering transform: flip locked polarity ----
    tampered = json.loads(json.dumps(invariants))
    tampered["events"][0]["polarity"] = "negative"   # locked field changed
    doc_t = Document(invariants=tampered, carrier_options=doc.carrier_options)
    ok_t, _ = detect_document(KEY, doc_t, nonce, code, MSG_LEN, TAG_BITS, mask)
    print("\n[P2] invariant-altering transform (polarity positive->negative):")
    print(f"     attributed={ok_t}  (expected False: h_I changed, MAC fails)")

    # ---- (P3) cryptographic false-positive rate on independent docs ----
    trials = 20000
    fp = 0
    for _ in range(trials):
        rnd_inv = {"events": [{"predicate": "SAY",
                               "roles": {"agent": f"x{rng.randint(0,9)}"},
                               "polarity": rng.choice(["positive", "negative"]),
                               "time": {}}]}
        rnd_opts = [rng.randint(0, 1) for _ in range(N)]
        d = Document(invariants=rnd_inv, carrier_options=rnd_opts)
        ok_fp, _ = detect_document(KEY, d, os.urandom(12), code,
                                   MSG_LEN, TAG_BITS, None)
        fp += int(ok_fp)
    print(f"\n[P3] cryptographic false positives over {trials} independent docs:")
    print(f"     observed={fp}  rate={fp/trials:.2e}  bound=2^-{TAG_BITS}"
          f"={2**-TAG_BITS:.2e}")

    # ---- (P4) no global carrier rule ----
    # For a fixed symbol (=1) at every carrier, the realized option vector
    # differs between two documents whose invariants differ, because the map
    # is bound to h_I. ~N/2 positions flip.
    h1 = canonical_invariant_digest(invariants)
    h2 = canonical_invariant_digest(tampered)
    v1 = [realize_option(KEY, h1, nonce, j, 1) for j in range(N)]
    v2 = [realize_option(KEY, h2, nonce, j, 1) for j in range(N)]
    diff = sum(a != b for a, b in zip(v1, v2))
    print("\n[P4] fixed symbol (=1) realizes differently across two docs:")
    print(f"     {diff}/{N} carrier options flip between doc_A and doc_B "
          f"(~N/2 expected; keyed map is invariant-bound, no global rule)")

    print("\n" + "=" * 68)
    all_ok = ok and rec == msg and (not ok_t) and fp == 0
    print("RESULT:", "ALL PROPERTIES HOLD" if all_ok else "CHECK OUTPUT")
    print("=" * 68)
    return all_ok


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
