# Ledger retrieval(+NLI) baseline vs typed meaning-digest (reviewer W1)

Same ledger assumption, same seeded closed-domain corpus (960 items). Backend: `bag-of-words`. Verification is id-addressed (each candidate is checked against its OWN registered source, exactly as the meaning-digest verifier looks up the ledger by id). Similarity methods are calibrated so benign-paraphrase acceptance is matched at ~0.95; we then read off single-field **tamper rejection**, the decisive axis. `retrieval` = cosine of candidate to its stored source; `+nli_proxy` adds a cheap directional token-coverage entailment gate; `+nli_oracle` is a perfect, unrealizable NLI ceiling that knows the gold contract.

| Method | Benign accept (TPR) | Single-field tamper rejection | Localizes field | Needs semantic model |
|---|---|---|---|---|
| Meaning-digest (typed) | 1.000 [0.996,1.000] | 1.000 [0.996,1.000] | yes | no |
| Retrieval (NN) | 0.941 [0.924,0.954] | 0.047 [0.035,0.062] | no | no |
| Retrieval + NLI (proxy) | 0.918 [0.899,0.933] | 0.061 [0.048,0.078] | no | yes |
| Retrieval + NLI (oracle ceiling) | 0.941 [0.924,0.954] | 1.000 [0.996,1.000] | no | yes |

Attribution rank-1 rate (nearest gallery entry is the true source): benign 0.424 [0.393,0.455], tamper 0.611 [0.580,0.642]. A tampered sentence is still nearest to its own source, so retrieval maps it back and cannot flag the edit; no similarity threshold separates a typed tamper from a legitimate paraphrase.

> Storing the source and retrieving it survives paraphrase but cannot reject a single-field meaning change: retrieval alone and a cheap NLI proxy leave the tamper accepted, and only a *perfect* (unrealizable) NLI matches the typed contract's tamper rejection --- yet even that neither localizes the changed field nor yields a keyed, unforgeable tag, both of which the typed meaning-digest provides deterministically with no model. Closed-domain, bag-of-words backend by default; a real encoder behaves the same on tamper (a one-field edit is embedding-close to its source).
