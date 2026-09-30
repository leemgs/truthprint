# Paraphrase and adaptive-attack robustness + extended-lexicon defense (RQ4 / RQ7)

Closed-domain, offline, seeded: 200 documents of 16 watermarked sentences are paraphrased on real English strings; meaning-digest provenance authentication is re-run on each paraphrase. `ValidRemoval` (Eq. validremoval) = meaning preserved (oracle gold contract) AND detection lost. The **closed** frontend is the Stage-2 lexicon; the **extended** frontend widens the English predicate/time/attribution inventory (coverage, not tolerance). `adv_novel` is a held-out attack whose synonyms lie outside the extended inventory too (the honest coverage bound).

## Headline: extended-lexicon frontend defends the adaptive attack

| Metric (contract core6) | Closed frontend | Extended frontend |
|---|---|---|
| Benign paraphrase auth TPR (RQ4) | 1.000 [1.000,1.000] | 1.000 [1.000,1.000] |
| **Adaptive ValidRemoval (RQ7)** | **1.000 [1.000,1.000]** | **0.000 [0.000,0.000]** |
| Adaptive auth TPR | 0.000 [0.000,0.000] | 1.000 [1.000,1.000] |
| Held-out novel ValidRemoval (coverage bound) | 1.000 [0.999,1.000] | 1.000 [0.999,1.000] |
| Altering-edit tamper rejection | 1.000 [0.999,1.000] | 1.000 [0.999,1.000] |

Reading: the closed lexicon lets the schema-aware adaptive attacker remove the mark (high ValidRemoval), but the extended-coverage frontend recovers the same invariants and drives adaptive ValidRemoval to ~0 while **still rejecting tampers** (coverage widened, tolerance not) and keeping benign paraphrase authenticated. This is direct evidence that the vulnerability is closed-lexicon coverage, not the meaning-digest principle. The held-out `adv_novel` attack still succeeds under both frontends: any *fixed* lexicon is evadable by an out-of-inventory synonym, which is why the general answer is the open-vocabulary neural frontend (`truthprint.neural_parser`, e.g. via `APIBackend`); the extension quantifies the mechanism (each added synonym family recovers authentication for that family).

## Per-operator detail

### Frontend `closed` (contract `core6`)

| Operator | Mode | Auth TPR | Doc attribution | ValidRemoval | Surface-carrier | Mean cosine |
|---|---|---|---|---|---|---|
| voice | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.880 [0.879,0.882] |
| time_reflow | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.922 [0.920,0.923] |
| verb_syn | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.042 [0.035,0.049] | 0.922 [0.920,0.923] |
| time_syn | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.041 [0.034,0.048] | 0.921 [0.919,0.922] |
| hedge | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.018 [0.014,0.024] | 0.910 [0.909,0.912] |
| combo_benign | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.879 [0.877,0.881] |
| adv_verb | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.894 [0.893,0.896] |
| adv_time | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.847 [0.845,0.850] |
| adv_combo | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.723 [0.721,0.725] |
| alter | altering | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] (tamper rej.) | 0.000 [0.000,0.001] | 0.889 [0.888,0.891] |
| adv_novel | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.805 [0.802,0.807] |

Residual adaptive-removal field breakdown (fields the `closed` frontend failed to recover): predicate: 9600, time_dir: 9600, quantity: 2200, attribution: 2154.

### Frontend `extended` (contract `core6`)

| Operator | Mode | Auth TPR | Doc attribution | ValidRemoval | Surface-carrier | Mean cosine |
|---|---|---|---|---|---|---|
| voice | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.880 [0.879,0.882] |
| time_reflow | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.922 [0.920,0.923] |
| verb_syn | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.042 [0.035,0.049] | 0.922 [0.920,0.923] |
| time_syn | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.041 [0.034,0.048] | 0.921 [0.919,0.922] |
| hedge | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.018 [0.014,0.024] | 0.910 [0.909,0.912] |
| combo_benign | benign | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.879 [0.877,0.881] |
| adv_verb | adaptive | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.894 [0.893,0.896] |
| adv_time | adaptive | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.847 [0.845,0.850] |
| adv_combo | adaptive | 1.000 [0.999,1.000] | 1.000 [0.981,1.000] | 0.000 [0.000,0.001] | 0.000 [0.000,0.001] | 0.723 [0.721,0.725] |
| alter | altering | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] (tamper rej.) | 0.000 [0.000,0.001] | 0.889 [0.888,0.891] |
| adv_novel | adaptive | 0.000 [0.000,0.001] | 0.000 [0.000,0.019] | 1.000 [0.999,1.000] | 0.000 [0.000,0.001] | 0.805 [0.802,0.807] |

Residual adaptive-removal field breakdown (fields the `extended` frontend failed to recover): time_dir: 3200, predicate: 3200, quantity: 673.

> Extended coverage is still a fixed lexicon (held-out `adv_novel` removal stays high); the open-vocabulary neural frontend is the general defense. Closed-domain Stage-2; wide-coverage paraphrase robustness at scale remains future work.
