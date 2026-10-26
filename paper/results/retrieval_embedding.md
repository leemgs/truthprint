# Ledger retrieval(+NLI) baseline vs typed meaning-digest (reviewer W1)

Same ledger assumption, same seeded closed-domain corpus (960 items). Backend: `embedding:minishlab/potion-multilingual-128M`. Verification is id-addressed (each candidate is checked against its OWN registered source, exactly as the meaning-digest verifier looks up the ledger by id). Similarity methods are calibrated so benign-paraphrase acceptance is matched at ~0.95; we then read off single-field **tamper rejection**, the decisive axis. `retrieval` = cosine of candidate to its stored source; `+nli_proxy` adds a cheap directional token-coverage entailment gate; `+nli_oracle` is a perfect, unrealizable NLI ceiling that knows the gold contract.

| Method | Benign accept (TPR) | Single-field tamper rejection | Needs semantic model |
|---|---|---|---|
| Meaning-digest (typed) | 1.000 [0.996,1.000] | 1.000 [0.996,1.000] | no |
| Retrieval (NN) | 0.947 [0.931,0.959] | 0.139 [0.118,0.162] | no |
| Retrieval + NLI (proxy) | 0.907 [0.887,0.924] | 0.151 [0.130,0.175] | yes |
| Retrieval + NLI (oracle ceiling) | 0.947 [0.931,0.959] | 1.000 [0.996,1.000] | yes |

Attribution rank-1 rate (nearest gallery entry is the true source): benign 0.641 [0.610,0.670], tamper 0.418 [0.387,0.449]. A tampered sentence is still nearest to its own source, so retrieval maps it back and cannot flag the edit; no similarity threshold separates a typed tamper from a legitimate paraphrase.

> Storing the source and retrieving it survives paraphrase but cannot reject a single-field meaning change: retrieval alone and a cheap NLI proxy leave the tamper accepted, and only a *perfect* (unrealizable) NLI matches the typed contract's tamper rejection, and it needs a semantic model where the typed meaning-digest decides deterministically with none. Closed-domain, bag-of-words backend by default; a real encoder behaves the same on tamper (a one-field edit is embedding-close to its source).
