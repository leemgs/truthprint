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

The four Korean mock reviews provide complementary ACL perspectives:
[`ACL_REVIEW_KO.md`](ACL_REVIEW_KO.md) focuses on empirical readiness,
[`ACL_REVIEW_2_KO.md`](ACL_REVIEW_2_KO.md) audits theoretical scope, security
games, nonce resolution, and novelty,
[`ACL_REVIEW_3_KO.md`](ACL_REVIEW_3_KO.md) re-judges the paper along the ARR
review-form axes (Soundness / Excitement / Reproducibility / Overall), reports a
reviewer reproduction of the artifact, and locates the honest track (main-track
with real experiments vs. Findings/workshop for the current design-and-core
contribution), and [`ACL_REVIEW_4_KO.md`](ACL_REVIEW_4_KO.md) simulates a full
review panel (3 reviewers + Area Chair) on the current paper and prioritizes the
remaining levers for an accept/publish outcome.

This repository bundles the reference implementation, the paper, and
supporting materials.

```
truthprint/
├── assets/     # project logo and shared images
├── code/       # reference implementation (Python, standard-library only) + tests
├── docs/       # Korean-language explainer homepage (GitHub Pages ready)
├── handoff/    # data handoff kit: what to collect for the real end-to-end eval
├── paper/      # IEEEtran LaTeX source, references, and compiled PDF
├── patent/     # patent presentation materials
└── ppt/        # project presentation slides
```

| Directory | Contents | Start here |
|---|---|---|
| [`code/`](code/) | The `truthprint` package, CLI, examples, tests, and CI. No runtime dependencies. | [`code/README.md`](code/README.md) |
| [`docs/`](docs/) | 한국어 소개 홈페이지 — a Korean-language explainer of the research idea, built from the project slides. Enable GitHub Pages on `/docs` to publish it. | [`docs/index.html`](docs/index.html) |
| [`paper/`](paper/) | *Truthprint: An Invariant-Constrained Semantic Intermediate Representation for Translation- and Paraphrase-Robust Provenance Watermarking* — LaTeX source (`main.tex`), `references.bib`, and `main.pdf`. | [`paper/README.md`](paper/README.md) |
| [`handoff/`](handoff/) | Data handoff kit — example sample files, a field schema, and a validator describing exactly what real MT/paraphrase outputs and human annotations to collect for the real multilingual end-to-end evaluation. | [`handoff/README_KO.md`](handoff/README_KO.md) |
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
truthprint selftest              # runs properties P1–P4 and L1–L3, prints PASS
pytest -q                        # full test suite
truthprint repro-table           # regenerate the erasure-cliff table
truthprint challenge             # field-level tamper vs. embedding ablation (C1–C3)
truthprint paraphrase            # paraphrase (RQ4) + adaptive-attack (RQ7) robustness
python scripts/eval_baselines.py # regenerate the baseline comparison (paper Tables V/VI)
python scripts/eval_challenge.py # regenerate the field-level challenge results
python scripts/eval_paraphrase.py # regenerate the paraphrase/adaptive-attack table
python scripts/eval_retrieval.py # regenerate the ledger retrieval(+NLI) baseline
python scripts/eval_neural_defense.py --use-cache # score the neural adaptive-defense from cache (no key)
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
| Bounded false positives | Cryptographic FP rate ≤ 2⁻ᵗᵃᵘ (0 observed over 20k trials at τ=32); the meaning-digest's operative floor is the *contract-collision* probability (contract entropy), not 2⁻ᵗᵃᵘ |
| Translation-robust authentication | Meaning-digest re-verifies a keyed tag over the invariant contract; survives real NLLB MT where surface carriers score 0/192 |
| Tamper localization | A single-field meaning change breaks verification and names the field; similarity / robust-hash / store-and-retrieve baselines cannot |
| Honest adaptive-attack accounting | Closed-lexicon removal is reported and localized; an extended-coverage frontend defends it (ValidRemoval 1.000→0.000) without weakening tamper rejection |
| Erasure resilience | Full payload recovery to 42% carrier erasure, collapsing at the rate-½ cliff (≈50%) |
| No global carrier rule | Keyed map is bound to (key, invariant digest, nonce) |

## Evaluation highlights (measured, reproducible)

Two provenance mechanisms share the IR; we report them **honestly and separately**.
Every number below regenerates from a fixed seed (see `paper/results/`).

- **Surface realization-carrier — honest negative under real MT.** Against real
  NLLB‑200 translation the Stage‑1 surface parser recovers **0/192** outputs:
  translation rewrites the carriers. (`paper/results/realmt_pilot.md`)
- **Meaning-digest — survives real translation.** A keyed tag over the typed
  invariant contract, re‑verified after transformation by a Stage‑2 multilingual
  extractor. On **4,800 real NLLB translations across six languages** (the full
  run is committed in‑repo under `paper/results/realmt_b2/`, so every number
  below reproduces from the raw data with no GPU): the Stage‑2 extractor recovers
  the invariant fields at **0.83–0.99** (closed categoricals — polarity, quantity,
  time, attribution — at **≥ 0.97**; the open entity/relational fields at
  **0.83–0.92**), core6 document‑level attribution is **1.000 for German/Hindi**
  and **0.90–0.98** for the rest (Arabic weakest), and tamper rejection is
  **≥ 0.996**.
  (`paper/results/provenance_realmt.md`, `paper/results/stage2_multilingual.md`,
  `paper/results/realmt_b2/`)
- **Real baseline comparison.** A real **KGW** token watermark collapses under real
  translation (clean 0.96 → **0.00–0.38** translated) while the meaning‑digest
  survives (**0.50–0.98**). At a matched 1% FPR, SemStamp survives round‑trip but
  degrades cross‑lingually, while the typed digest survives and — unlike
  similarity/robust hashing — rejects single‑field tampers.
  (`paper/results/baselines_real.md`, `paper/results/semantic_baselines.md`)
- **Paraphrase & adaptive attack (RQ4/RQ7).** Benign meaning‑preserving paraphrase
  authenticates (TPR **1.000**); a schema‑aware adaptive attacker that swaps
  out‑of‑lexicon synonyms removes the mark under the closed lexicon (ValidRemoval
  **1.000**) — an honest negative localized to lexicon coverage (polarity and agent
  still survive). (`paper/results/paraphrase.md`)
- **Extended-lexicon defense.** A broader‑coverage frontend drives adaptive
  ValidRemoval **1.000 → 0.000** while keeping benign auth and tamper rejection at
  **1.000** (coverage widened, not tolerance); a held‑out out‑of‑inventory attack
  still evades any *fixed* lexicon → the general answer is the open‑vocabulary
  neural frontend. (`paper/results/paraphrase.md`)
- **Open-vocabulary neural frontend closes the held-out gap (two models).** Real
  instruction LLMs (GPT‑4o‑mini $N{=}40$ and Llama‑3.3‑70B $N{=}10$ via an
  OpenAI‑compatible API, schema‑guided) drive the **held‑out novel** adaptive
  ValidRemoval from **1.000** (both fixed lexicons) to **0.050 / 0.100** (CIs
  disjoint from the lexicons’) at benign/tamper **1.000** — they read the
  invariants from out‑of‑inventory synonyms a fixed lexicon cannot. Neural
  extractions are cached, so scoring reproduces with no key.
  (`paper/results/neural_defense.md`, `paper/results/neural_defense_gpt4omini.md`)
- **“Why not just store & retrieve?”** Under the *same* ledger, retrieval and a
  cheap NLI proxy reject **≤ 0.06** of single‑field tampers at matched benign
  acceptance; only a *perfect (unrealizable)* NLI matches the typed contract’s
  **1.000** tamper rejection, and even then cannot localize the field or give a
  keyed tag. (`paper/results/retrieval.md`)

> All positive results are **closed‑domain and small‑scale**. Wide‑coverage neural
> parsing, broader official baselines (SynthID, SWAN), open‑vocabulary adaptive
> robustness, and human evaluation remain future work.

## Diagnostic Stage-1 simulation (appendix — superseded by the real-MT results above)

In a shared closed-domain diagnostic simulation (`code/scripts/eval_baselines.py`,
paper Appendix A), method-inspired proxies respond to stipulated channel parameters. The outputs validate simulator behavior; they are not real translation results or method rankings:

| Method | Signal layer | Clean-text TPR | Translation TPR (EN→KO) |
|---|---|---|---|
| KGW proxy | token identity | 1.00 | **0.02** |
| DEW | edit-aligned token | 1.00 | **0.00** |
| SemStamp | sentence embedding | 1.00 | 0.99 |
| SWAN | AMR / meaning | 1.00 | 1.00 |
| **Truthprint** | **invariant + MAC** | **1.00** | **1.00** (simulated channel; authenticates) |

> Diagnostic simulation, not a neural or translation benchmark: each baseline is a
> method-inspired proxy evaluated on the same simulated channel. End-to-end
> evaluation with official implementations and real transformations is future work.

## Scope & limitations

- The linguistic layer is a **closed-domain, rule-based** Stage-1 demonstrator.
  It proves the pipeline round-trips on real strings; it is **not** a
  wide-coverage semantic parser.
- All positive translation/paraphrase results use a **closed-domain, lexicon-based
  Stage-2 extractor**. A schema-aware adaptive attacker with out-of-lexicon
  synonyms defeats any *fixed* lexicon (an extended lexicon only widens coverage),
  so **open-vocabulary neural parsing is required** for general adaptive robustness.
- The meaning-digest's false-positive floor is the **contract-collision
  probability** (governed by contract entropy on the deployment text), not the
  2⁻ᵗᵃᵘ cryptographic bound; estimate it per corpus before deployment.
- Binary carriers only in this reference; higher-arity carriers are a natural
  extension.
- Truthprint provides **authenticated attribution designed for transformation robustness**; it
  does **not** claim cryptographic *undetectability*.

## Contributing

Issues and PRs are welcome — especially wider-coverage parsers, new carrier
families, additional languages, and attack evaluations. Please run
`pytest -q` and `truthprint selftest` (from `code/`) before submitting.

## License & citation

MIT licensed (see [`code/LICENSE`](code/LICENSE)). If you use this work, please
cite the accompanying paper (see [`code/CITATION.cff`](code/CITATION.cff)).
