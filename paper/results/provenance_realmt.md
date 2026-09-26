# Meaning-based provenance authentication on real MT output

Verifier re-extracts invariants (Stage-2) and checks a keyed 32-bit tag over an invariant contract; the tag lives in an out-of-band ledger, not the text. Contrast: the surface-carrier pilot scored 0/192. FPR bound per test = 2^-tau.

## Contract `core6` = ['polarity', 'quantity', 'time_dir', 'attribution', 'predicate', 'agent']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.656 [0.580,0.725] | 0.900 [0.596,0.982] | 0.988 [0.956,0.997] | 0.006 [0.001,0.035] |
| de (de) | 0.975 [0.937,0.990] | 1.000 [0.722,1.000] | 1.000 [0.977,1.000] | 0.006 [0.001,0.035] |
| hi (hi) | 0.944 [0.897,0.970] | 1.000 [0.722,1.000] | 1.000 [0.977,1.000] | 0.006 [0.001,0.035] |
| ko (ko) | 0.969 [0.929,0.987] | 1.000 [0.722,1.000] | 1.000 [0.977,1.000] | 0.013 [0.003,0.044] |
| rt (en) | 0.931 [0.881,0.961] | 1.000 [0.722,1.000] | 1.000 [0.977,1.000] | 0.006 [0.001,0.035] |
| zh (zh) | 0.950 [0.904,0.974] | 1.000 [0.722,1.000] | 0.994 [0.965,0.999] | 0.000 [0.000,0.023] |

## Contract `robust7` = ['agent', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.656 [0.580,0.725] | 0.900 [0.596,0.982] | 0.988 [0.956,0.997] | 0.000 [0.000,0.023] |
| de (de) | 0.800 [0.731,0.855] | 1.000 [0.722,1.000] | 0.975 [0.937,0.990] | 0.006 [0.001,0.035] |
| hi (hi) | 0.938 [0.889,0.966] | 1.000 [0.722,1.000] | 1.000 [0.977,1.000] | 0.000 [0.000,0.023] |
| ko (ko) | 0.863 [0.801,0.907] | 1.000 [0.722,1.000] | 0.994 [0.965,0.999] | 0.000 [0.000,0.023] |
| rt (en) | 0.800 [0.731,0.855] | 1.000 [0.722,1.000] | 0.981 [0.946,0.994] | 0.006 [0.001,0.035] |
| zh (zh) | 0.850 [0.787,0.897] | 1.000 [0.722,1.000] | 0.988 [0.956,0.997] | 0.000 [0.000,0.023] |

## Contract `full9` = ['agent', 'patient', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution', 'causation']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.344 [0.275,0.420] | 0.200 [0.057,0.510] | 1.000 [0.977,1.000] | 0.000 [0.000,0.023] |
| de (de) | 0.800 [0.731,0.855] | 1.000 [0.722,1.000] | 0.994 [0.965,0.999] | 0.000 [0.000,0.023] |
| hi (hi) | 0.881 [0.822,0.923] | 1.000 [0.722,1.000] | 1.000 [0.977,1.000] | 0.000 [0.000,0.023] |
| ko (ko) | 0.856 [0.794,0.902] | 1.000 [0.722,1.000] | 1.000 [0.977,1.000] | 0.000 [0.000,0.023] |
| rt (en) | 0.744 [0.671,0.805] | 1.000 [0.722,1.000] | 0.988 [0.956,0.997] | 0.000 [0.000,0.023] |
| zh (zh) | 0.806 [0.738,0.860] | 1.000 [0.722,1.000] | 1.000 [0.977,1.000] | 0.000 [0.000,0.023] |

> Meaning-based authentication survives real translation where the surface carrier does not; a wider contract authenticates more meaning but is more sensitive to extraction noise (fidelity/robustness trade-off). Closed-domain Stage-2; wide-coverage parsing is future work.
