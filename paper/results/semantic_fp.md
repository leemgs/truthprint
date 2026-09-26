# Semantic-collision false-positive floor (meaning-digest provenance)

Closed-domain corpus: 800 sampled facts (seed 7). Cryptographic tag bound at tau=32 bits is 2^-32 = 2.33e-10.

The meaning-digest scheme authenticates when a re-extracted invariant contract reproduces a keyed tag, so the achievable false-positive rate is bounded below by the probability that two *distinct* legitimate generations share the same contract digest -- the contract-collision floor. This floor is governed by the entropy of the chosen contract on the deployment text, **not** by tau.

| Contract | Fields | |C| | Max entropy | Observed distinct | Shannon H | Collision H2 | **Collision floor** | vs 2^-tau |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `core6` | 6 fields | 192 | 7.58 b | 191 | 7.42 b | 7.29 b | **5.15e-03** | 2.21e+07x |
| `robust7` | 7 fields | 576 | 9.17 b | 436 | 8.58 b | 8.39 b | **1.73e-03** | 7.42e+06x |
| `full9` | 9 fields | 6912 | 12.75 b | 748 | 9.51 b | 9.45 b | **1.75e-04** | 7.53e+05x |

## Finding

The `core6` contract-collision floor (5.15e-03, ~1/192) matches the 0.001--0.010 false positives reported for real MT in the provenance evaluation. Those false positives are therefore the **contract-collision floor, not the cryptographic 2^-32 bound** -- they differ by ~2.2e+07x. Widening the contract lowers the floor (full9 reaches ~1e-4) at the cost of translation robustness.

## Caveat

This uniform closed-domain corpus is an *upper* bound on contract entropy. Real, non-templated text -- especially short or formulaic sentences -- has lower entropy and therefore a *higher* collision floor. Estimating contract entropy per corpus is a deployment prerequisite; the cryptographic bound applies only once contract entropy exceeds tau bits.
