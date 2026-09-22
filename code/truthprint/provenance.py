"""Meaning-based provenance authentication (translation-robust, no surface carrier).

The real-MT pilot showed surface carriers (voice/time-position) do not survive
translation. This module implements the paper's actual objective --- *verifying
consistency with a participating keyed generator* --- on the **meaning layer**
instead of a hidden surface payload.

At generation time the producer registers, per sentence, a keyed tag over the
canonical digest of a declared *invariant contract* (a chosen subset of the
typed fields):

    tag_i = truncate(HMAC_K(canonical(I_contract(sentence_i)) || nonce || i), tau)

The tag lives in an out-of-band provenance ledger (as the paper specifies for
the nonce), not in the text. At detection time the verifier re-extracts the
invariants from the (possibly translated) sentence with the Stage-2 multilingual
extractor, recomputes the tag, and authenticates iff it matches. Authentication
therefore succeeds exactly when the contract's fields are recovered correctly
from the transformed text --- which the Stage-2 extractor achieves at high rates
on real MT (Section stage2). A meaning-altering edit changes a contract field,
so the tag no longer matches (tamper rejection); an unrelated document matches
only with probability 2^-tau (cryptographic false-positive bound).

Choosing the contract trades fidelity coverage for robustness: a wider contract
authenticates more meaning but is more sensitive to extraction noise. This module
makes that trade explicit and measurable (see scripts/eval_provenance.py).
"""
from __future__ import annotations

import hashlib
import hmac
import json

__all__ = ["CONTRACTS", "contract_digest", "register_tag", "authenticate",
           "document_attribution"]

# Named invariant contracts (field subsets), from robust to full.
CONTRACTS = {
    "core6": ["polarity", "quantity", "time_dir", "attribution", "predicate",
              "agent"],
    "robust7": ["agent", "predicate", "polarity", "quantity", "time_dir",
                "modality", "attribution"],
    "full9": ["agent", "patient", "predicate", "polarity", "quantity",
              "time_dir", "modality", "attribution", "causation"],
}


def contract_digest(invariants: dict, fields: list[str]) -> bytes:
    """SHA-256 over the canonical JSON of the contract's fields only."""
    proj = {k: invariants.get(k) for k in fields}
    blob = json.dumps(proj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).digest()


def _tag(key: bytes, invariants: dict, nonce: bytes, sent_id: str,
         fields: list[str], tag_bits: int) -> bytes:
    d = contract_digest(invariants, fields)
    msg = d + nonce + sent_id.encode("utf-8")
    full = hmac.new(key, msg, hashlib.sha256).digest()
    nbytes = (tag_bits + 7) // 8
    return full[:nbytes]


def register_tag(key: bytes, gold_invariants: dict, nonce: bytes, sent_id: str,
                 contract: str = "core6", tag_bits: int = 32) -> bytes:
    """Producer-side ledger entry for one sentence."""
    return _tag(key, gold_invariants, nonce, sent_id, CONTRACTS[contract],
                tag_bits)


def authenticate(key: bytes, observed_invariants: dict, nonce: bytes,
                 sent_id: str, registered_tag: bytes, contract: str = "core6",
                 tag_bits: int = 32) -> bool:
    """Verifier-side check: do the re-extracted invariants reproduce the tag?"""
    cand = _tag(key, observed_invariants, nonce, sent_id, CONTRACTS[contract],
                tag_bits)
    return hmac.compare_digest(cand, registered_tag)


def document_attribution(authenticated_flags: list[bool],
                         min_fraction: float = 0.5) -> bool:
    """Attribute a document if at least ``min_fraction`` of its sentences
    individually authenticate (erasure-tolerant document decision)."""
    if not authenticated_flags:
        return False
    return (sum(authenticated_flags) / len(authenticated_flags)) >= min_fraction
