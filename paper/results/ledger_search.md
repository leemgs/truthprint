# Id-free ledger search on real MT output

The verifier receives only a translated document and searches the whole ledger (50 documents, 800 sentences) with the same Stage-2 extractor, 32-bit keyed tags and >= 50% document rule as `eval_provenance.py`, but with no document or sentence id. Wilson 95% CI.

## Contract `core6` = ['polarity', 'quantity', 'time_dir', 'attribution', 'predicate', 'agent']

| Condition | Sentence matches a wrong entry | Doc true attribution (id-free) | Doc false attribution per pair | Docs with any false attribution |
|---|---|---|---|---|
| ar (ar) | 0.771 [0.741,0.799] | 0.900 [0.786,0.957] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| de (de) | 0.844 [0.817,0.867] | 1.000 [0.929,1.000] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| hi (hi) | 0.871 [0.846,0.893] | 1.000 [0.929,1.000] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| ko (ko) | 0.690 [0.657,0.721] | 0.960 [0.865,0.989] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| rt (en) | 0.736 [0.705,0.766] | 1.000 [0.929,1.000] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| zh (zh) | 0.656 [0.623,0.688] | 0.940 [0.838,0.979] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |

## Contract `robust7` = ['agent', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution']

| Condition | Sentence matches a wrong entry | Doc true attribution (id-free) | Doc false attribution per pair | Docs with any false attribution |
|---|---|---|---|---|
| ar (ar) | 0.595 [0.561,0.628] | 0.900 [0.786,0.957] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| de (de) | 0.626 [0.592,0.659] | 0.940 [0.838,0.979] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| hi (hi) | 0.652 [0.619,0.685] | 1.000 [0.929,1.000] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| ko (ko) | 0.521 [0.487,0.556] | 0.700 [0.562,0.809] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| rt (en) | 0.547 [0.513,0.582] | 0.800 [0.670,0.888] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| zh (zh) | 0.485 [0.451,0.520] | 0.740 [0.604,0.841] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |

## Contract `full9` = ['agent', 'patient', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution', 'causation']

| Condition | Sentence matches a wrong entry | Doc true attribution (id-free) | Doc false attribution per pair | Docs with any false attribution |
|---|---|---|---|---|
| ar (ar) | 0.046 [0.034,0.063] | 0.020 [0.004,0.105] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| de (de) | 0.096 [0.078,0.119] | 0.940 [0.838,0.979] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| hi (hi) | 0.076 [0.060,0.097] | 0.940 [0.838,0.979] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| ko (ko) | 0.087 [0.070,0.109] | 0.300 [0.191,0.438] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| rt (en) | 0.075 [0.059,0.095] | 0.240 [0.143,0.374] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |
| zh (zh) | 0.055 [0.041,0.073] | 0.080 [0.032,0.188] | 0.000 [0.000,0.002] (n=2450) | 0.000 [0.000,0.071] |

> Sentence-level search is not usable on its own: with a per-pair contract-collision floor near 1/192, a sentence collides with some wrong entry of a large ledger. The document rule is what keeps id-free attribution specific; the per-pair rate is the quantity that scales with ledger size.
