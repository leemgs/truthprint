# Translator-independent (embedding) frontend vs lexicon (Task 1 / W5)

Categorical invariant recovery on cached **real** LLM-MT translations (96 sentences), split by domain. The neural column is a real multilingual **embedding** frontend that is *model-separated from the translator*; the lexicon column is the in-repo Stage-2 extractor on the same text. Wilson 95% CI.

## Domain: open

| Field | Neural (sep.) | Lexicon |
|---|---|---|
| polarity | 0.500 [0.345,0.655] | 1.000 [0.904,1.000] |
| time_dir | 0.944 [0.819,0.985] | 0.000 [0.000,0.096] |
| modality | 0.472 [0.320,0.630] | 1.000 [0.904,1.000] |
| causation | 0.528 [0.370,0.680] | 0.778 [0.619,0.883] |
| attribution | 0.528 [0.370,0.680] | 0.694 [0.531,0.820] |
| **aggregate** | **0.594** | **0.694** |

## Domain: template

| Field | Neural (sep.) | Lexicon |
|---|---|---|
| polarity | 0.600 [0.474,0.714] | 0.983 [0.911,0.997] |
| time_dir | 0.800 [0.682,0.882] | 1.000 [0.940,1.000] |
| modality | 0.417 [0.301,0.543] | 0.833 [0.720,0.907] |
| causation | 0.350 [0.242,0.476] | 1.000 [0.940,1.000] |
| attribution | 0.650 [0.524,0.758] | 1.000 [0.940,1.000] |
| **aggregate** | **0.563** | **0.963** |

> Open-domain temporal direction is the decisive cell: the lexicon abstains on out-of-vocabulary time wording while the translator-independent embedding frontend recovers it. A static embedding is nonetheless insufficient for the full typed contract, motivating the instruction-LLM frontend run on the separated-backend GPU harness (handoff/).
