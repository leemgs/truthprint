# Meaning-based provenance authentication on real MT output

Verifier re-extracts invariants (Stage-2) and checks a keyed 32-bit tag over an invariant contract; the tag lives in an out-of-band ledger, not the text. Contrast: the surface-carrier pilot scored 0/192. FPR bound per test = 2^-tau.

## Contract `core6` = ['polarity', 'quantity', 'time_dir', 'attribution', 'predicate', 'agent']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.629 [0.595,0.662] | 0.920 [0.812,0.968] | 0.999 [0.993,1.000] | 0.001 [0.000,0.007] |
| de (de) | 0.968 [0.953,0.978] | 1.000 [0.929,1.000] | 1.000 [0.995,1.000] | 0.005 [0.002,0.013] |
| hi (hi) | 0.946 [0.928,0.960] | 1.000 [0.929,1.000] | 0.993 [0.984,0.997] | 0.006 [0.003,0.015] |
| ko (ko) | 0.968 [0.953,0.978] | 1.000 [0.929,1.000] | 1.000 [0.995,1.000] | 0.010 [0.005,0.020] |
| rt (en) | 0.936 [0.917,0.951] | 1.000 [0.929,1.000] | 0.995 [0.987,0.998] | 0.004 [0.001,0.011] |
| zh (zh) | 0.955 [0.938,0.967] | 1.000 [0.929,1.000] | 0.999 [0.993,1.000] | 0.005 [0.002,0.013] |

## Contract `robust7` = ['agent', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.629 [0.595,0.662] | 0.920 [0.812,0.968] | 0.995 [0.987,0.998] | 0.000 [0.000,0.005] |
| de (de) | 0.812 [0.784,0.838] | 1.000 [0.929,1.000] | 0.996 [0.989,0.999] | 0.003 [0.001,0.009] |
| hi (hi) | 0.945 [0.927,0.959] | 1.000 [0.929,1.000] | 0.991 [0.982,0.996] | 0.003 [0.001,0.009] |
| ko (ko) | 0.863 [0.837,0.885] | 1.000 [0.929,1.000] | 0.989 [0.979,0.994] | 0.001 [0.000,0.007] |
| rt (en) | 0.807 [0.779,0.833] | 1.000 [0.929,1.000] | 0.983 [0.971,0.990] | 0.003 [0.001,0.009] |
| zh (zh) | 0.860 [0.834,0.882] | 1.000 [0.929,1.000] | 0.994 [0.985,0.997] | 0.000 [0.000,0.005] |

## Contract `full9` = ['agent', 'patient', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution', 'causation']

| Condition | Sentence TPR (95% CI) | Document attribution | Tamper rejection | False positive |
|---|---|---|---|---|
| ar (ar) | 0.289 [0.258,0.321] | 0.080 [0.032,0.188] | 0.994 [0.985,0.997] | 0.000 [0.000,0.005] |
| de (de) | 0.812 [0.784,0.838] | 1.000 [0.929,1.000] | 0.996 [0.989,0.999] | 0.000 [0.000,0.005] |
| hi (hi) | 0.880 [0.856,0.901] | 1.000 [0.929,1.000] | 0.995 [0.987,0.998] | 0.000 [0.000,0.005] |
| ko (ko) | 0.858 [0.832,0.880] | 1.000 [0.929,1.000] | 0.996 [0.989,0.999] | 0.000 [0.000,0.005] |
| rt (en) | 0.770 [0.740,0.798] | 1.000 [0.929,1.000] | 0.995 [0.987,0.998] | 0.000 [0.000,0.005] |
| zh (zh) | 0.829 [0.801,0.853] | 1.000 [0.929,1.000] | 0.996 [0.989,0.999] | 0.000 [0.000,0.005] |

> Meaning-based authentication survives real translation where the surface carrier does not; a wider contract authenticates more meaning but is more sensitive to extraction noise (fidelity/robustness trade-off). Closed-domain Stage-2; wide-coverage parsing is future work.
