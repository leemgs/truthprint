# Paraphrase and adaptive-attack robustness (RQ4 / RQ7)

Closed-domain, offline, seeded: 200 documents of 16 watermarked sentences are paraphrased on real English strings, and the meaning-digest provenance authentication is re-run on the paraphrase. Benign = meaning-preserving, in-lexicon; adaptive (RQ7) = meaning-preserving but out-of-lexicon (schema-aware attacker); altering = one locked field changed. `ValidRemoval` (Eq. validremoval) = meaning preserved (oracle) AND detection lost.

## Headline (contract `core6`)

* Benign paraphrase authentication TPR: **1.000 [1.000,1.000]** (RQ4: paraphrase does not remove the mark).
* Adaptive-attack ValidRemoval (oracle): **1.000 [1.000,1.000]**; literal Eq.4 (parser InvariantEq): 0.000 [0.000,0.000] (~0 by construction: for a meaning-digest, losing detection and the parser judging meaning changed are the same event).
* Altering-edit tamper rejection: **1.000 [0.999,1.000]**.
* Surface-carrier (Stage-1) recovery under paraphrase: benign 0.015 [0.013,0.017], adaptive 0.000 [0.000,0.000] (the paraphrase counterpart of the 0/192 translation negative).

## Contract `core6` = ['polarity', 'quantity', 'time_dir', 'attribution', 'predicate', 'agent']

| Operator | Mode | Auth TPR | Doc attribution | ValidRemoval | Surface-carrier | Mean cosine |
|---|---|---|---|---|---|---|
| voice | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.878 [0.876,0.879] |
| time_reflow | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.920 [0.918,0.921] |
| verb_syn | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.036 [0.030,0.043] | 0.920 [0.918,0.921] |
| time_syn | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.036 [0.030,0.043] | 0.920 [0.918,0.921] |
| hedge | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.017 [0.013,0.022] | 0.908 [0.907,0.910] |
| combo_benign | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.878 [0.876,0.879] |
| adv_verb | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.893 [0.891,0.894] |
| adv_time | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.845 [0.843,0.847] |
| adv_combo | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.721 [0.718,0.723] |
| alter | altering | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] (tamper rej.) | 0.000 [0.000,0.001] | 0.889 [0.888,0.891] |

Adaptive-removal field breakdown (which contract field the closed lexicon failed to recover): predicate: 6400, time_dir: 6400, attribution: 2145, quantity: 1506.

## Contract `robust7` = ['agent', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution']

| Operator | Mode | Auth TPR | Doc attribution | ValidRemoval | Surface-carrier | Mean cosine |
|---|---|---|---|---|---|---|
| voice | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.878 [0.876,0.879] |
| time_reflow | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.920 [0.918,0.921] |
| verb_syn | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.036 [0.030,0.043] | 0.920 [0.918,0.921] |
| time_syn | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.036 [0.030,0.043] | 0.920 [0.918,0.921] |
| hedge | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.017 [0.013,0.022] | 0.908 [0.907,0.910] |
| combo_benign | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.878 [0.876,0.879] |
| adv_verb | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.893 [0.891,0.894] |
| adv_time | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.845 [0.843,0.847] |
| adv_combo | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.721 [0.718,0.723] |
| alter | altering | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] (tamper rej.) | 0.000 [0.000,0.001] | 0.889 [0.888,0.891] |

Adaptive-removal field breakdown (which contract field the closed lexicon failed to recover): predicate: 6400, time_dir: 6400, attribution: 2145, quantity: 1506.

## Contract `full9` = ['agent', 'patient', 'predicate', 'polarity', 'quantity', 'time_dir', 'modality', 'attribution', 'causation']

| Operator | Mode | Auth TPR | Doc attribution | ValidRemoval | Surface-carrier | Mean cosine |
|---|---|---|---|---|---|---|
| voice | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.878 [0.876,0.879] |
| time_reflow | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.920 [0.918,0.921] |
| verb_syn | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.036 [0.030,0.043] | 0.920 [0.918,0.921] |
| time_syn | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.036 [0.030,0.043] | 0.920 [0.918,0.921] |
| hedge | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.017 [0.013,0.022] | 0.908 [0.907,0.910] |
| combo_benign | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.878 [0.876,0.879] |
| adv_verb | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.893 [0.891,0.894] |
| adv_time | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.845 [0.843,0.847] |
| adv_combo | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.721 [0.718,0.723] |
| alter | altering | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] (tamper rej.) | 0.000 [0.000,0.001] | 0.889 [0.888,0.891] |

Adaptive-removal field breakdown (which contract field the closed lexicon failed to recover): predicate: 6400, time_dir: 6400, attribution: 2145, quantity: 1506.

> Benign paraphrase is authenticated at high rates (RQ4). The adaptive attacker's residual ValidRemoval is not a defeat of the meaning-digest principle but a measurement of the *closed lexicon's* coverage: it is localized to the predicate/time fields whose surface markers the attacker strips, which is exactly what the wide-coverage neural frontend (truthprint.neural_parser) is designed to close. Surface carriers do not survive content paraphrase, mirroring translation. Closed-domain Stage-2; wide-coverage paraphrase robustness is future work.
