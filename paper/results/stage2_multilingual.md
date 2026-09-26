# Stage-2 multilingual invariant extractor on real MT output

Field-level recovery of the typed invariants from **real** NLLB translations, per condition (ko/hi = direct translation; rt = round-trip English). Wilson 95% CIs. Contrast: the Stage-1 surface parser recovers 0/192 (Section real-MT pilot).

## Aggregate field recovery (all conditions)

| Field | Recovery (95% CI) | |
|---|---|---|
| agent | 0.997 [0.995, 0.998] | `####################` |
| patient | 0.905 [0.896, 0.913] | `##################..` |
| predicate | 0.960 [0.954, 0.965] | `###################.` |
| polarity | 0.992 [0.989, 0.994] | `####################` |
| quantity | 0.974 [0.969, 0.978] | `###################.` |
| time_dir | 0.997 [0.995, 0.998] | `####################` |
| modality | 0.910 [0.902, 0.918] | `##################..` |
| attribution | 0.969 [0.964, 0.974] | `###################.` |
| causation | 0.975 [0.971, 0.979] | `####################` |

## Per-condition detail

| Condition (lang) | agent | patient | predicate | polarity | quantity | time_dir | modality | attribution | causation | all-exact |
|---|---|---|---|---|---|---|---|---|---|---|
| ar (ar) | 0.99 | 0.50 | 0.87 | 1.00 | 0.86 | 1.00 | 0.99 | 0.84 | 0.99 | 0.29 |
| de (de) | 1.00 | 1.00 | 0.97 | 1.00 | 1.00 | 1.00 | 0.83 | 1.00 | 1.00 | 0.81 |
| hi (hi) | 0.99 | 1.00 | 0.98 | 0.98 | 1.00 | 0.99 | 1.00 | 1.00 | 0.92 | 0.88 |
| ko (ko) | 1.00 | 1.00 | 0.98 | 1.00 | 0.98 | 1.00 | 0.90 | 1.00 | 0.99 | 0.86 |
| rt (en) | 1.00 | 0.97 | 0.99 | 0.98 | 1.00 | 0.99 | 0.85 | 0.97 | 0.95 | 0.77 |
| zh (zh) | 1.00 | 0.96 | 0.96 | 0.99 | 1.00 | 1.00 | 0.89 | 1.00 | 1.00 | 0.83 |

> Meaning-layer fields (polarity, quantity, temporal direction, attribution, causation, modality) survive real translation and are recoverable by a lexicon-level semantic frontend; entities a translator renders inconsistently (e.g. config drift) are recovered less reliably. This is a closed-domain Stage-2 result, not a wide-coverage parser.
