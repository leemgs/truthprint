# Meaning-based provenance authentication on real MT output

Verifier re-extracts invariants (Stage-2) and checks a keyed 32-bit tag over an invariant contract; the tag lives in an out-of-band ledger, not the text. Contrast: the surface-carrier parser reads 1/4,800 translations. The tag adds a 2^-tau forgery bound; the measured false-positive rate is set by contract collisions (low-entropy records), not by 2^-tau.

## Contract `core6` = ['polarity', 'quantity', 'time_dir', 'attribution', 'predicate', 'agent']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.619 [0.585,0.652] | 0.900 [0.786,0.957] | 0.996 [0.989,0.999] | 0.000 [0.000,0.005] |
| de (de) | 0.850 [0.824,0.873] | 1.000 [0.929,1.000] | 1.000 [0.995,1.000] | 0.004 [0.001,0.011] |
| hi (hi) | 0.901 [0.879,0.920] | 1.000 [0.929,1.000] | 1.000 [0.995,1.000] | 0.006 [0.003,0.015] |
| ko (ko) | 0.684 [0.651,0.715] | 0.940 [0.838,0.979] | 1.000 [0.995,1.000] | 0.007 [0.003,0.016] |
| rt (en) | 0.720 [0.688,0.750] | 0.980 [0.895,0.996] | 0.998 [0.991,0.999] | 0.003 [0.001,0.009] |
| zh (zh) | 0.666 [0.633,0.698] | 0.940 [0.838,0.979] | 1.000 [0.995,1.000] | 0.005 [0.002,0.013] |

## Contract `robust7` = ['agent', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.616 [0.582,0.649] | 0.900 [0.786,0.957] | 0.994 [0.985,0.997] | 0.001 [0.000,0.007] |
| de (de) | 0.660 [0.626,0.692] | 0.940 [0.838,0.979] | 0.991 [0.982,0.996] | 0.004 [0.001,0.011] |
| hi (hi) | 0.894 [0.870,0.913] | 1.000 [0.929,1.000] | 0.998 [0.991,0.999] | 0.004 [0.001,0.011] |
| ko (ko) | 0.537 [0.503,0.572] | 0.700 [0.562,0.809] | 0.990 [0.980,0.995] | 0.001 [0.000,0.007] |
| rt (en) | 0.568 [0.533,0.601] | 0.820 [0.692,0.902] | 0.993 [0.984,0.997] | 0.003 [0.001,0.009] |
| zh (zh) | 0.540 [0.505,0.574] | 0.720 [0.583,0.825] | 0.996 [0.989,0.999] | 0.000 [0.000,0.005] |

## Contract `full9` = ['agent', 'patient', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution', 'causation']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.256 [0.227,0.288] | 0.020 [0.004,0.105] | 0.995 [0.987,0.998] | 0.000 [0.000,0.005] |
| de (de) | 0.659 [0.625,0.691] | 0.940 [0.838,0.979] | 0.996 [0.989,0.999] | 0.000 [0.000,0.005] |
| hi (hi) | 0.694 [0.661,0.725] | 0.940 [0.838,0.979] | 0.999 [0.993,1.000] | 0.000 [0.000,0.005] |
| ko (ko) | 0.416 [0.383,0.451] | 0.320 [0.208,0.458] | 0.990 [0.980,0.995] | 0.000 [0.000,0.005] |
| rt (en) | 0.383 [0.349,0.417] | 0.280 [0.175,0.417] | 0.993 [0.984,0.997] | 0.000 [0.000,0.005] |
| zh (zh) | 0.325 [0.293,0.358] | 0.080 [0.032,0.188] | 0.989 [0.979,0.994] | 0.000 [0.000,0.005] |

> Meaning-based authentication survives real translation where the surface carrier does not; a wider contract authenticates more meaning but is more sensitive to extraction noise (fidelity/robustness trade-off). Closed-domain Stage-2; wide-coverage parsing is future work.
