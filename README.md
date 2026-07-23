<p align="center">
  <img src="assets/truthprint-logo.svg" alt="Truthprint logo" width="560">
</p>

# Truthprint

**Invariant-constrained semantic provenance watermarking for LLM-generated text.**

Truthprint carries a watermark in the *meaning* of text rather than in its
tokens. It locks the truth-conditional content of a passage (entities,
predicates, roles, polarity, quantities, time, attribution) into a typed
**invariant contract**, then encodes an **authenticated, error-corrected
payload** using only the realization freedom that does *not* change that
contract. Because the signal lives above the token surface, it is designed to
survive meaning-preserving transformations such as **paraphrasing and
translation** — where token-level watermarks degrade — while remaining
**machine-readable and unforgeable**.

[![ci](https://github.com/leemgs/truthprint/actions/workflows/ci.yml/badge.svg)](https://github.com/leemgs/truthprint/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](code/LICENSE)

> Shared in the spirit of *Hongik Ingan* ("benefit all humankind"): a reference
> implementation to help researchers reproduce, critique, and build on the idea.
> It is research-grade, not a turnkey production system.

---

## Why this matters

The EU AI Act (Regulation (EU) 2024/1689), Article 50, requires providers of
generative systems to mark synthetic outputs — **text included** — in a
*machine-readable* format that is *detectable* as AI-generated, effective
August 2026. A mark that is machine-readable yet trivially erased by
translation or paraphrasing does not meet that intent. Truthprint targets
exactly this gap: a durable, authenticated provenance mark.

## Repository layout

This repository bundles the reference implementation, the paper, and
supporting materials.

```
truthprint/
├── assets/     # project logo and shared images
├── code/       # reference implementation (Python, standard-library only) + tests
├── paper/      # IEEEtran LaTeX source, references, and compiled PDF
├── patent/     # patent presentation materials
└── ppt/        # project presentation slides
```

| Directory | Contents | Start here |
|---|---|---|
| [`code/`](code/) | The `truthprint` package, CLI, examples, tests, and CI. No runtime dependencies. | [`code/README.md`](code/README.md) |
| [`paper/`](paper/) | *Truthprint: An Invariant-Constrained Semantic Intermediate Representation for Translation- and Paraphrase-Robust Provenance Watermarking* — LaTeX source (`main.tex`), `references.bib`, and `main.pdf`. | [`paper/README.md`](paper/README.md) |
| [`patent/`](patent/) | Patent presentation deck. | — |
| [`ppt/`](ppt/) | Project presentation slides. | — |

---

## Getting started

The core is pure Python (≥ 3.9, standard library only). `pytest` is only needed
to run the test suite.

```bash
git clone https://github.com/leemgs/truthprint
cd truthprint/code
python -m pip install -e ".[dev]"     # editable install + pytest
```

### 60-second check

```bash
truthprint selftest          # runs properties P1–P4 and L1–L3, prints PASS
pytest -q                    # full test suite
truthprint repro-table       # regenerate the erasure-cliff table
```

### Build the paper

```bash
cd paper
make                         # runs pdflatex twice -> main.pdf
```

See [`code/README.md`](code/README.md) for the API, worked examples, and the
architecture diagrams; see [`paper/README.md`](paper/README.md) for the paper's
formal analysis and reproducibility notes.

---

## Key properties

| Property | What it means |
|---|---|
| Semantic fidelity by construction | Watermarking never alters locked meaning; carriers with no valid realization become erasures |
| Unforgeability | Forging attribution reduces to forging the MAC (HMAC-SHA256) |
| Bounded false positives | Cryptographic FP rate ≤ 2⁻ᵗᵃᵘ (0 observed over 20k trials at τ=32) |
| Erasure resilience | Full payload recovery up to a code-rate-dependent erasure cliff |
| No global carrier rule | Keyed map is bound to (key, invariant digest, nonce) |

## Scope & limitations

- The linguistic layer is a **closed-domain, rule-based** Stage-1 demonstrator.
  It proves the pipeline round-trips on real strings; it is **not** a
  wide-coverage semantic parser.
- Binary carriers only in this reference; higher-arity carriers are a natural
  extension.
- Truthprint provides **authenticated, transformation-robust attribution**; it
  does **not** claim cryptographic *undetectability*.

## Contributing

Issues and PRs are welcome — especially wider-coverage parsers, new carrier
families, additional languages, and attack evaluations. Please run
`pytest -q` and `truthprint selftest` (from `code/`) before submitting.

## License & citation

MIT licensed (see [`code/LICENSE`](code/LICENSE)). If you use this work, please
cite the accompanying paper (see [`code/CITATION.cff`](code/CITATION.cff)).
