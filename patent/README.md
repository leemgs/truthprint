# Patent Application Materials — Truthprint

This directory contains the invention disclosure draft prepared for patent application
of the Truthprint semantic provenance watermarking method and system.

## File

| File | Description |
|---|---|
| `truthprint-patent-20260723.pptx` | Invention disclosure deck (Korean, 13 slides) — draft for patent attorney review |

## Invention title

| Language | Title |
|---|---|
| 국문 | 의미 불변식 계약 기반 번역·패러프레이즈 강건 텍스트 출처 워터마킹 방법 및 장치 |
| English | Invariant-Constrained Semantic Provenance Watermarking for Robust Text Attribution |

Reference number: **TP-2026-001**

## Technical field

AI-generated text provenance marking and detection — natural language processing and
information security, specifically machine-readable provenance attribution for the
output of generative language models.

## Summary of the invention

Truthprint locks the truth-conditional meaning of a text passage (entities, predicates,
polarity, quantities, time, causality, attribution) into a typed **invariant contract**,
then encodes an **authenticated payload**

```
p = m ‖ MAC_K(m ∥ n ∥ h_I)
```

using only the realization freedom that does *not* change that contract (e.g., active
vs. passive voice, word order, clause packaging). The payload is distributed across
multiple sentence-level carriers via a systematic GF(2) erasure code, so that even if
a portion of carriers is lost through translation or paraphrasing, the payload is
recovered. Because the invariant digest `h_I` binds the payload, any transformation
that damages the locked meaning causes MAC verification to fail automatically.

## Claim structure (summary)

| Claim | Type | Subject |
|---|---|---|
| 1 | Independent — Method | Watermarking method (extract invariant → authenticate → ECC encode → keyed realization) |
| 8 | Independent — Apparatus | Encoding unit (100) + Detection unit (200) |
| 15 | Independent — Medium | Computer-readable recording medium storing the method |
| 2–7, 9–14, 16 | Dependent | `h_I` binding, erasure decoding, MAC attribution, mutability types, cross-lingual normalization, statistical fallback |

## System components (Figure 1)

```
Encoding unit (100)                         Detection unit (200)
  110 IR generation                           210 Parsing
  120 Invariant locking    ─── text ───>      220 Normalization
  130 Authentication (MAC)                    230 Inverse mapping (erasure marking)
  140 ECC encoding                            240 ECC decoding  p̂
  150 Keyed carrier realization               250 MAC verification → attribution
       shared: secret key K, nonce n, invariant digest h_I
```

## Advantages over prior art

| | Prior art | Truthprint |
|---|---|---|
| Carrier | Token statistics / embeddings | Realization freedom of typed invariant contract |
| Robustness | Fragile under translation / paraphrase | Resilient via distribution + ECC + erasure decoding |
| Attribution | Statistical threshold test | MAC verification (unforgeable) |
| Meaning protection | None explicit | Truth-conditional invariant bound to `h_I`, auto-detected |

### Measured supporting evidence (deck slides 12–13)

The disclosure now cites the Stage-1 reference-implementation measurements
(from [`code/scripts/eval_baselines.py`](../code/)) as support for the inventive
step — under a shared translation channel, prior-art token watermarks collapse
while the invention survives and additionally authenticates:

| Method (signal layer) | Translation TPR |
|---|---|
| SynthID-Text/KGW, DEW (token) | 0.00 – 0.02 (collapses) |
| SemStamp (embedding), SWAN (AMR) | 0.99 – 1.00 (survives, no authentication) |
| **Truthprint (invariant + MAC)** | **1.00 + authenticated / unforgeable** |

## Status and next steps

> **This deck is a draft for patent attorney review.** Claim language and scope must
> be finalized by a registered patent attorney before filing. Inventor name and
> applicant institution fields are left blank pending confirmation.

- [ ] Fill in inventor name(s) and applicant institution on slide 1
- [ ] Submit to patent attorney for claim drafting and prior-art search
- [ ] Confirm drawings (Figures 1–3) meet the formality requirements of the target
      filing office (KR, US, PCT, etc.)
- [ ] Coordinate filing timeline with EU AI Act enforcement date (August 2026)

## Relation to other materials

| Directory | Relation |
|---|---|
| [`paper/`](../paper/) | IEEE Transactions on Computers manuscript — provides formal proofs (Thm. 1–2, Prop. 1–2) that support the novelty and inventive step arguments |
| [`code/`](../code/) | Reference implementation — verifies properties P1–P4 and L1–L3 cited in the disclosure |
| [`docs/`](../docs/) | Korean-language public explainer (GitHub Pages) |
