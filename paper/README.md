# Paper — Truthprint

**Truthprint: An Invariant-Constrained Semantic Intermediate Representation for
Translation- and Paraphrase-Robust Provenance Watermarking**

Manuscript formatted for *IEEE Transactions on Computers*
(`\documentclass[journal]{IEEEtran}`).

---

## Files

| File | Description |
|---|---|
| `main.tex` | Complete manuscript source |
| `IEEEtran.cls` | Local IEEEtran class file for reproducible compilation |
| `references.bib` | BibTeX database (kept in sync with the inline `thebibliography`) |
| `main.pdf` | Compiled preview (11 pages) |
| `Makefile` | Build and cleanup commands |
| `reference/truthprint_poc.py` | Self-contained Python reference core (stdlib only) |
| `reference/truthprint_linguistic_demo.py` | Linguistic layer end-to-end demo |

---

## Build the paper

```bash
make
```

Equivalent:

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Two passes are required for cross-references and the bibliography.

---

## Run the reference implementation

Both scripts use only the Python standard library.

### Core properties (P1–P4)

```bash
python3 reference/truthprint_poc.py
```

Verifies four properties of the language-independent coding/crypto layer:

| ID | Property |
|---|---|
| P1 | Full payload recovery with 28/96 (~29%) carriers erased |
| P2 | Invariant binding — altering a locked field fails the MAC |
| P3 | ~2⁻ᵗᵃᵘ cryptographic false-positive rate (0 / 20,000 trials at τ = 32) |
| P4 | Keyed carrier map is invariant-bound (43/96 options differ across documents) |

### Linguistic layer (L1–L3)

```bash
python3 reference/truthprint_linguistic_demo.py
```

Exercises the closed-domain Stage-1 linguistic pipeline on real sentence strings
(voice and time-position carriers):

| ID | Property |
|---|---|
| L1 | Invariant fidelity through benign rewrites |
| L2 | Payload recovery under carrier erasure (19/64 erased) |
| L3 | Tamper detection under negation |

Both scripts exit non-zero on failure and double as regression tests.

---

## Paper structure

| Section | Content |
|---|---|
| Introduction | Motivation (EU AI Act Art. 50), problem statement, contributions |
| Background | Semantic IR, token-level and embedding-based watermarks, cryptographic watermarks |
| Method | Invariant contract, authenticated payload, ECC encoding, keyed carrier map |
| Formal Analysis | Prop. 1 (semantic fidelity), Thm. 1 (unforgeability), Thm. 2 (FP bound), Prop. 2 (erasure cliff) |
| Implementation | Packaged CLI, erasure-cliff table (measured), P1–P4 and L1–L3 |
| Deployment | Inline vs. asynchronous, graceful degradation, per-paragraph localization |
| Evaluation matrix | Research questions mapped to decisive comparisons and outcome measures |
| Limitations | Stage-1 parser scope, binary carriers, undetectability not claimed |
| Future work | Wide-coverage frontend, higher-arity carriers, multilingual interlingua |

---

## Reproducibility

The "Reproducibility and Notation" section pins every primitive:

| Primitive | Specification | Code identifier |
|---|---|---|
| Invariant digest `h_I` | SHA-256 over canonical JSON | `invariants.canonical_digest` |
| Authenticated payload `p` | HMAC-SHA256 truncated to τ bits | `payload.authenticate_payload` |
| Keyed carrier map | `a*_j = π_j ⊕ c_j` | `carriers.keyed_bit` |
| ECC | Systematic `[n, k]` GF(2) + erasure decode | `coding.GF2Code` |

All randomness is seeded; every reported number reproduces from the scripts above.
Environment: Python 3 (standard library only) and TeX Live with `pdflatex`.

The packaged CLI (see [`code/`](../code/)) provides equivalent commands:

```bash
truthprint selftest        # P1–P4 and L1–L3
truthprint repro-table     # erasure-cliff table
```

---

## References

The bibliography contains 26 verified references with clickable URLs
(`\hypersetup{colorlinks,urlcolor=blue}`). Notable citations:

- **SynthID-Text** (Nature 634) — state-of-the-art token-level watermark
- **Shumailov et al.** (Nature 631) — model collapse from unattributed synthetic data
- **EU AI Act** (Regulation (EU) 2024/1689), Article 50 — regulatory context

---

## Research integrity note

The paper does **not** fabricate LLM detection results. Every reported number
(P1–P4, L1–L3, the erasure-cliff table, and the Table V/VI detection and
translation-robustness values) is measured by code in this repository and
reproducible from a fixed seed.

Tables V and VI are a **controlled Stage-1 comparison, not a neural benchmark**:
Truthprint and the four baselines (SynthID-Text/KGW, DEW, SemStamp, SWAN) are run
from one shared harness (`code/scripts/eval_baselines.py`) on the same
closed-domain testbed under one shared meaning-preserving channel. The baselines
are faithful reductions of each method's *detection statistic* and *signal
placement*; they abstract the neural frontend (LM sampler, sentence encoder, AMR
parser) exactly as the Truthprint Stage-1 numbers do. Full neural-scale
evaluation with a wide-coverage semantic frontend remains the paper's future
work, and the tables carry `†` footnotes stating this scope.

---

## Author metadata

The author name and contact e-mail are set in `main.tex`. Before submission, fill in
the affiliation (and IEEE membership grade / funding acknowledgement if applicable)
in the `\thanks{}` block — see the `TODO` comment next to `\author{}` in `main.tex`.
