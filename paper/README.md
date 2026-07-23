# Truthprint IEEEtran LaTeX Project

This directory contains an IEEE journal-style LaTeX manuscript (formatted for
*IEEE Transactions on Computers*) for:

**Truthprint: An Invariant-Constrained Semantic Intermediate Representation for Translation- and Paraphrase-Robust Provenance Watermarking**

## Files

- `main.tex`: complete manuscript using `\documentclass[journal]{IEEEtran}`
- `IEEEtran.cls`: local IEEEtran class file for reproducible compilation
- `references.bib`: BibTeX database (kept in sync with the inline `thebibliography`)
- `reference/truthprint_poc.py`: self-contained, dependency-free reference
  implementation of the language-independent core (invariant digest,
  authenticated payload, keyed carrier assignment, GF(2) erasure decoding)
- `Makefile`: build and cleanup commands
- `main.pdf`: compiled preview

## Build the paper

```bash
make
```

Equivalent command:

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

## Run the reference implementation

The proof-of-concept uses only the Python standard library:

```bash
python3 reference/truthprint_poc.py
```

It verifies four properties referenced in the paper (Sec. "Reference
Implementation and Verification"): (P1) full payload recovery with 28/96
(~29%) carriers erased, (P2) invariant binding — altering a locked field fails the
MAC, (P3) ~2^-tau cryptographic false-positive rate measured over 20,000
independent documents, and (P4) the keyed carrier map is invariant-bound
(no global rule). It exits non-zero if any property fails, so it doubles as
a regression test.

A second script exercises the linguistic layer end to end on actual sentence
strings (voice + time-position carriers) for the closed-domain Stage-1 setting:

```bash
python3 reference/truthprint_linguistic_demo.py
```

It verifies invariant fidelity (L1), payload recovery under carrier erasure
(L2), and tamper detection under negation (L3). It also doubles as a
regression test (non-zero exit on failure).

## What changed in this revision

This revision strengthens the draft along four axes without fabricating any
experimental result:

1. **Formal analysis (new section).** Semantic fidelity by construction
   (Prop. 1), payload unforgeability by reduction to MAC EUF-CMA (Thm. 1),
   a cryptographic false-positive bound of 2^-tau (Thm. 2), an
   erasure-channel capacity model with a recovery cliff at the code rate
   (Prop. 2), and a complexity analysis.
2. **Novelty framing.** An explicit metric-vs-typed-predicate distinction
   from embedding-based semantic watermarks, and a positioning subsection on
   provable/cryptographic watermarking (KGW, Unigram, distortion-free,
   undetectable).
3. **Implementation verification.** A runnable reference core plus a measured
   erasure-tolerance table that empirically confirms the capacity cliff.
   These are properties of the coding/crypto layer, NOT detection-performance
   claims on model text.
4. **Practicality.** A deployment-path subsection (inline vs. asynchronous,
   graceful degradation, layered fallback to token-level watermarks for
   low-capacity spans, per-paragraph localization and abstention).
5. **Presentation and concreteness.** A system data-flow figure (TikZ), a
   worked linguistic example (active/passive + translation erasure), a
   closed-domain linguistic round-trip demo verified on real strings, and an
   evaluation matrix mapping each research question to its decisive comparison
   and outcome measure.

## Reproducibility

The paper's "Reproducibility and Notation" section pins every primitive used
by the reference implementation (SHA-256 canonical-JSON invariant digest,
HMAC-SHA256 tag, keyed carrier map a* = pi_j XOR c_j, systematic GF(2) code
with GF(2) erasure decoding) and gives a symbol-to-identifier table so the
formalism and the code in `reference/` agree exactly. All randomness is
seeded, so every reported number reproduces; the per-run nonce does not affect
recovery. Environment: Python 3 (standard library only) and TeX Live with
`pdflatex`.

## References and regulatory framing (this revision)

- The bibliography now contains 26 verified references, each with a clickable
  URL rendered in blue (`\hypersetup{colorlinks,urlcolor=blue}`) so reviewers
  can confirm existence and read the sources before submission.
- Nature-published work is included: the SynthID-Text paper (Nature 634) and
  the model-collapse paper (Shumailov et al., Nature 631), which motivates the
  need for reliable provenance.
- The Introduction and Background now motivate the work against the EU AI Act
  (Regulation (EU) 2024/1689), whose Article 50 requires machine-readable,
  detectable marking of AI-generated text from August 2026 — a robustness
  requirement that fragile token-level marks do not meet.
- `references.bib` is kept in sync with the inline `thebibliography`.

## Important research note

The paper intentionally does not fabricate LLM detection results. The
clean-text and translation result tables are explicitly framed as evaluation
*protocol templates*; their `TBD` cells are to be populated once the
wide-coverage semantic frontend (identified in the paper as future work)
exists. The reference-implementation numbers (erasure tolerance, cryptographic
false positives, P1–P4 and L1–L3) ARE real, were regenerated from the code in
this repository, and are clearly scoped to the language-independent core.

## Author metadata

The author name and contact e-mail are set in `main.tex`. Before submission,
fill in the affiliation (and IEEE membership grade / funding, if applicable)
in the `\thanks{}` block — see the `TODO` comment next to `\author{}`.
