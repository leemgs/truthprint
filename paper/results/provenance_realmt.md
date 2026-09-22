# Meaning-based provenance authentication on real MT output

Verifier re-extracts invariants (Stage-2) and checks a keyed 32-bit tag over an invariant contract; the tag lives in an out-of-band ledger, not the text. Contrast: the surface-carrier pilot scored 0/192. FPR bound per test = 2^-tau.

## Contract `core6` = ['polarity', 'quantity', 'time_dir', 'attribution', 'predicate', 'agent']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| hi (hi) | 0.953 [0.871,0.984] | 1.000 [0.510,1.000] | 1.000 [0.943,1.000] | 0.016 [0.003,0.083] |
| ko (ko) | 0.797 [0.683,0.877] | 1.000 [0.510,1.000] | 0.984 [0.917,0.997] | 0.016 [0.003,0.083] |
| rt (en) | 0.828 [0.718,0.901] | 1.000 [0.510,1.000] | 0.984 [0.917,0.997] | 0.000 [0.000,0.057] |

## Contract `robust7` = ['agent', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| hi (hi) | 0.859 [0.754,0.924] | 1.000 [0.510,1.000] | 1.000 [0.943,1.000] | 0.000 [0.000,0.057] |
| ko (ko) | 0.703 [0.582,0.801] | 1.000 [0.510,1.000] | 1.000 [0.943,1.000] | 0.000 [0.000,0.057] |
| rt (en) | 0.766 [0.649,0.853] | 1.000 [0.510,1.000] | 0.984 [0.917,0.997] | 0.016 [0.003,0.083] |

## Contract `full9` = ['agent', 'patient', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution', 'causation']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| hi (hi) | 0.734 [0.615,0.827] | 1.000 [0.510,1.000] | 0.984 [0.917,0.997] | 0.000 [0.000,0.057] |
| ko (ko) | 0.625 [0.503,0.733] | 1.000 [0.510,1.000] | 0.969 [0.893,0.991] | 0.000 [0.000,0.057] |
| rt (en) | 0.688 [0.566,0.788] | 1.000 [0.510,1.000] | 0.969 [0.893,0.991] | 0.000 [0.000,0.057] |

> Meaning-based authentication survives real translation where the surface carrier does not; a wider contract authenticates more meaning but is more sensitive to extraction noise (fidelity/robustness trade-off). Closed-domain Stage-2; wide-coverage parsing is future work.
