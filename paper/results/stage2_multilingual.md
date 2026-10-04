# Stage-2 multilingual invariant extractor on real MT output

Field-level recovery of the typed invariants from **real** NLLB translations, per condition (ko/hi = direct translation; rt = round-trip English). Wilson 95% CIs. Contrast: the Stage-1 surface parser recovers 0/192 (Section real-MT pilot).

## Aggregate field recovery (all conditions)

| Field | Recovery (95% CI) | |
|---|---|---|
| agent | 0.923 [0.915, 0.930] | `##################..` |
| patient | 0.825 [0.814, 0.836] | `#################...` |
| predicate | 0.868 [0.858, 0.877] | `#################...` |
| polarity | 0.995 [0.993, 0.997] | `####################` |
| quantity | 0.975 [0.970, 0.979] | `####################` |
| time_dir | 0.971 [0.966, 0.976] | `###################.` |
| modality | 0.860 [0.850, 0.869] | `#################...` |
| attribution | 0.973 [0.968, 0.977] | `###################.` |
| causation | 0.854 [0.844, 0.864] | `#################...` |

## Per-condition detail

| Condition (lang) | agent | patient | predicate | polarity | quantity | time_dir | modality | attribution | causation | all-exact |
|---|---|---|---|---|---|---|---|---|---|---|
| ar (ar) | 1.00 | 0.40 | 0.79 | 1.00 | 0.89 | 1.00 | 0.99 | 0.85 | 1.00 | 0.25 |
| de (de) | 1.00 | 1.00 | 0.86 | 1.00 | 0.99 | 1.00 | 0.76 | 1.00 | 1.00 | 0.66 |
| hi (hi) | 0.98 | 0.82 | 0.94 | 1.00 | 1.00 | 0.96 | 0.98 | 1.00 | 0.92 | 0.69 |
| ko (ko) | 0.82 | 0.95 | 0.85 | 0.99 | 0.98 | 1.00 | 0.82 | 1.00 | 0.74 | 0.41 |
| rt (en) | 0.83 | 0.85 | 0.92 | 0.98 | 1.00 | 0.97 | 0.79 | 0.98 | 0.70 | 0.38 |
| zh (zh) | 0.90 | 0.92 | 0.85 | 1.00 | 1.00 | 0.89 | 0.82 | 1.00 | 0.77 | 0.33 |

> Meaning-layer fields (polarity, quantity, temporal direction, attribution, causation, modality) survive real translation and are recoverable by a lexicon-level semantic frontend; entities a translator renders inconsistently (e.g. config drift) are recovered less reliably. This is a closed-domain Stage-2 result, not a wide-coverage parser.
