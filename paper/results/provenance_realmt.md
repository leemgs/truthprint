# Meaning-based provenance authentication on real MT output

Verifier re-extracts invariants (Stage-2) and checks a keyed 32-bit tag over an invariant contract; the tag lives in an out-of-band ledger, not the text. Contrast: the surface-carrier pilot scored 0/192. FPR bound per test = 2^-tau.

## Contract `core6` = ['polarity', 'quantity', 'time_dir', 'attribution', 'predicate', 'agent']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.656 [0.580,0.725] | 0.900 [0.596,0.982] | 0.988 [0.956,0.997] | 0.006 [0.001,0.035] |
| de (de) | 0.794 [0.725,0.849] | 1.000 [0.722,1.000] | 1.000 [0.977,1.000] | 0.006 [0.001,0.035] |
| hi (hi) | 0.944 [0.897,0.970] | 1.000 [0.722,1.000] | 1.000 [0.977,1.000] | 0.006 [0.001,0.035] |
| ko (ko) | 0.850 [0.787,0.897] | 1.000 [0.722,1.000] | 0.981 [0.946,0.994] | 0.013 [0.003,0.044] |
| rt (en) | 0.825 [0.759,0.876] | 1.000 [0.722,1.000] | 0.975 [0.937,0.990] | 0.006 [0.001,0.035] |
| zh (zh) | 0.644 [0.567,0.714] | 0.900 [0.596,0.982] | 0.981 [0.946,0.994] | 0.000 [0.000,0.023] |

## Contract `robust7` = ['agent', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.656 [0.580,0.725] | 0.900 [0.596,0.982] | 0.988 [0.956,0.997] | 0.000 [0.000,0.023] |
| de (de) | 0.644 [0.567,0.714] | 1.000 [0.722,1.000] | 0.988 [0.956,0.997] | 0.006 [0.001,0.035] |
| hi (hi) | 0.700 [0.625,0.766] | 1.000 [0.722,1.000] | 0.975 [0.937,0.990] | 0.000 [0.000,0.023] |
| ko (ko) | 0.744 [0.671,0.805] | 1.000 [0.722,1.000] | 0.969 [0.929,0.987] | 0.000 [0.000,0.023] |
| rt (en) | 0.637 [0.561,0.708] | 1.000 [0.722,1.000] | 0.956 [0.912,0.979] | 0.006 [0.001,0.035] |
| zh (zh) | 0.550 [0.473,0.625] | 0.700 [0.397,0.892] | 0.981 [0.946,0.994] | 0.000 [0.000,0.023] |

## Contract `full9` = ['agent', 'patient', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution', 'causation']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.344 [0.275,0.420] | 0.200 [0.057,0.510] | 1.000 [0.977,1.000] | 0.000 [0.000,0.023] |
| de (de) | 0.644 [0.567,0.714] | 1.000 [0.722,1.000] | 0.994 [0.965,0.999] | 0.000 [0.000,0.023] |
| hi (hi) | 0.650 [0.573,0.720] | 1.000 [0.722,1.000] | 0.981 [0.946,0.994] | 0.000 [0.000,0.023] |
| ko (ko) | 0.681 [0.606,0.748] | 1.000 [0.722,1.000] | 0.994 [0.965,0.999] | 0.000 [0.000,0.023] |
| rt (en) | 0.594 [0.516,0.667] | 0.900 [0.596,0.982] | 0.975 [0.937,0.990] | 0.000 [0.000,0.023] |
| zh (zh) | 0.494 [0.417,0.570] | 0.500 [0.237,0.763] | 1.000 [0.977,1.000] | 0.000 [0.000,0.023] |

> Meaning-based authentication survives real translation where the surface carrier does not; a wider contract authenticates more meaning but is more sensitive to extraction noise (fidelity/robustness trade-off). Closed-domain Stage-2; wide-coverage parsing is future work.
