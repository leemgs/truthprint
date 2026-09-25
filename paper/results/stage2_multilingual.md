# Stage-2 multilingual invariant extractor on real MT output

Field-level recovery of the typed invariants from **real** NLLB translations, per condition (ko/hi = direct translation; rt = round-trip English). Wilson 95% CIs. Contrast: the Stage-1 surface parser recovers 0/192 (Section real-MT pilot).

## Aggregate field recovery (all conditions)

| Field | Recovery (95% CI) | |
|---|---|---|
| agent | 0.996 [0.989, 0.998] | `####################` |
| patient | 0.899 [0.878, 0.916] | `##################..` |
| predicate | 0.932 [0.915, 0.947] | `###################.` |
| polarity | 0.950 [0.934, 0.962] | `###################.` |
| quantity | 0.956 [0.941, 0.967] | `###################.` |
| time_dir | 0.997 [0.991, 0.999] | `####################` |
| modality | 0.841 [0.816, 0.862] | `#################...` |
| attribution | 0.939 [0.922, 0.952] | `###################.` |
| causation | 0.957 [0.943, 0.968] | `###################.` |

## Per-condition detail

| Condition (lang) | agent | patient | predicate | polarity | quantity | time_dir | modality | attribution | causation | all-exact |
|---|---|---|---|---|---|---|---|---|---|---|
| ar (ar) | 0.98 | 0.54 | 0.89 | 1.00 | 0.88 | 1.00 | 0.99 | 0.84 | 0.99 | 0.34 |
| de (de) | 1.00 | 1.00 | 0.79 | 1.00 | 1.00 | 1.00 | 0.77 | 1.00 | 1.00 | 0.64 |
| hi (hi) | 0.99 | 1.00 | 0.97 | 0.97 | 1.00 | 1.00 | 0.73 | 1.00 | 0.92 | 0.65 |
| ko (ko) | 1.00 | 1.00 | 0.98 | 0.87 | 0.99 | 1.00 | 0.89 | 1.00 | 0.90 | 0.68 |
| rt (en) | 1.00 | 0.94 | 0.99 | 0.86 | 1.00 | 0.98 | 0.79 | 0.98 | 0.94 | 0.59 |
| zh (zh) | 1.00 | 0.91 | 0.96 | 0.99 | 0.87 | 1.00 | 0.88 | 0.81 | 1.00 | 0.49 |

> Meaning-layer fields (polarity, quantity, temporal direction, attribution, causation, modality) survive real translation and are recoverable by a lexicon-level semantic frontend; entities a translator renders inconsistently (e.g. config drift) are recovered less reliably. This is a closed-domain Stage-2 result, not a wide-coverage parser.
