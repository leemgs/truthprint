# Meaning-based provenance authentication on real MT output

Verifier re-extracts invariants (Stage-2) and checks a keyed 32-bit tag over an invariant contract; the tag lives in an out-of-band ledger, not the text. Contrast: the surface-carrier pilot scored 0/192. FPR bound per test = 2^-tau.

## Contract `core6` = ['polarity', 'quantity', 'time_dir', 'attribution', 'predicate', 'agent']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.618 [0.583,0.651] | 0.900 [0.786,0.957] | 0.996 [0.989,0.999] | 0.000 [0.000,0.005] |
| de (de) | 0.850 [0.824,0.873] | 1.000 [0.929,1.000] | 1.000 [0.995,1.000] | 0.004 [0.001,0.011] |
| hi (hi) | 0.886 [0.862,0.906] | 1.000 [0.929,1.000] | 1.000 [0.995,1.000] | 0.004 [0.001,0.011] |
| ko (ko) | 0.682 [0.649,0.714] | 0.940 [0.838,0.979] | 1.000 [0.995,1.000] | 0.007 [0.003,0.016] |
| rt (en) | 0.723 [0.690,0.752] | 0.980 [0.895,0.996] | 0.998 [0.991,0.999] | 0.003 [0.001,0.009] |
| zh (zh) | 0.666 [0.633,0.698] | 0.940 [0.838,0.979] | 1.000 [0.995,1.000] | 0.005 [0.002,0.013] |

## Contract `robust7` = ['agent', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.615 [0.581,0.648] | 0.900 [0.786,0.957] | 0.994 [0.985,0.997] | 0.001 [0.000,0.007] |
| de (de) | 0.656 [0.623,0.688] | 0.940 [0.838,0.979] | 0.991 [0.982,0.996] | 0.004 [0.001,0.011] |
| hi (hi) | 0.879 [0.854,0.900] | 1.000 [0.929,1.000] | 0.998 [0.991,0.999] | 0.004 [0.001,0.011] |
| ko (ko) | 0.532 [0.498,0.567] | 0.680 [0.542,0.792] | 0.990 [0.980,0.995] | 0.001 [0.000,0.007] |
| rt (en) | 0.564 [0.529,0.598] | 0.780 [0.648,0.872] | 0.993 [0.984,0.997] | 0.003 [0.001,0.009] |
| zh (zh) | 0.540 [0.505,0.574] | 0.700 [0.562,0.809] | 0.996 [0.989,0.999] | 0.000 [0.000,0.005] |

## Contract `full9` = ['agent', 'patient', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution', 'causation']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.253 [0.224,0.284] | 0.020 [0.004,0.105] | 0.995 [0.987,0.998] | 0.000 [0.000,0.005] |
| de (de) | 0.655 [0.621,0.687] | 0.940 [0.838,0.979] | 0.996 [0.989,0.999] | 0.000 [0.000,0.005] |
| hi (hi) | 0.685 [0.652,0.716] | 0.940 [0.838,0.979] | 0.999 [0.993,1.000] | 0.000 [0.000,0.005] |
| ko (ko) | 0.414 [0.380,0.448] | 0.300 [0.191,0.438] | 0.990 [0.980,0.995] | 0.000 [0.000,0.005] |
| rt (en) | 0.378 [0.345,0.412] | 0.240 [0.143,0.374] | 0.993 [0.984,0.997] | 0.000 [0.000,0.005] |
| zh (zh) | 0.326 [0.295,0.360] | 0.080 [0.032,0.188] | 0.989 [0.979,0.994] | 0.000 [0.000,0.005] |

> Meaning-based authentication survives real translation where the surface carrier does not; a wider contract authenticates more meaning but is more sensitive to extraction noise (fidelity/robustness trade-off). Closed-domain Stage-2; wide-coverage parsing is future work.
