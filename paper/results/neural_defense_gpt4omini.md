# Wide-coverage neural frontend defends the adaptive attack (open vocabulary)

Same seeded closed-domain adaptive corpus (40 items, contract `core6`, Wilson 95% CI). Three frontends, identical text: the closed lexicon, the extended lexicon, and a real instruction LLM (`openai/gpt-4o-mini`). `ValidRemoval` = meaning preserved AND detection lost (lower is better); `held-out novel` uses synonyms outside the extended inventory. Neural extractions are cached for reproducible scoring (0 live API calls this run).

| Frontend | Benign TPR | Adaptive-seen ValidRemoval | Held-out novel ValidRemoval | Tamper rejection |
|---|---|---|---|---|
| closed | 1.000 [0.912,1.000] | 1.000 [0.969,1.000] | 1.000 [0.912,1.000] | 1.000 [0.912,1.000] |
| extended | 1.000 [0.912,1.000] | 0.000 [0.000,0.031] | 1.000 [0.912,1.000] | 1.000 [0.912,1.000] |
| neural | 1.000 [0.912,1.000] | 0.050 [0.023,0.105] | 0.050 [0.014,0.165] | 1.000 [0.912,1.000] |

> The closed lexicon is removed by the adaptive attack; the extended lexicon defends the *seen* synonyms but not the held-out novel ones (any fixed lexicon is escapable); the **open-vocabulary neural frontend defends both** --- it recovers the invariants from out-of-inventory synonyms --- while preserving benign authentication and tamper rejection. This closes the adaptive-robustness gap the fixed lexicons leave open. Closed-domain; a wider-domain, larger-scale neural run is the next step.

Example adaptive-combo sentences and recovered `predicate` / `time_dir` by frontend (closed vs extended vs neural):

- *On one day later, 5 cache misss was cleared up by the engineer to prevent the outage.* → closed `None/None`, extended `FIX/following`, neural `FIX/following`
- *As the merchant put it, the operator must have sorted out the memory leak to prevent the outage on one day later.* → closed `None/None`, extended `FIX/following`, neural `FIX/following`
- *Per the internal memo, the developer did not clear up 2 server errors to prevent the outage on 24 hours later.* → closed `None/None`, extended `FIX/following`, neural `FIX/following`
