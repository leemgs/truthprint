# Same-text fact fidelity (extractor-based proxy)

Proxy: Stage-2 extractor reads back the source core6 record (clean English); 480 sentences per variant; Wilson 95% CI. A mismatch may be a dropped fact or unread wording; no human judgment.

| Variant | core6 read back |
|---|---|
| Unwatermarked, first sample | 0.617 [0.572,0.659] |
| KGW | 0.477 [0.433,0.522] |
| SynthID-Text | 0.498 [0.453,0.542] |
| Truthprint (validated, up to 4 draws) | 0.871 [0.838,0.898] |

Truthprint draws per sentence: mean 1.79, histogram {'1': 296, '2': 72, '3': 29, '4': 83}; 62 sentences had no valid realization.
