# Same-text fluency proxy (perplexity under GPT-2)

480 clean English sentences per variant, scored by `openai-community/gpt2` (not the generator). Geometric-mean perplexity with a 95% CI, and the paired mean difference in log-perplexity to the unwatermarked first sample (> 0 means less predictable wording). An automatic proxy, not a human quality judgment.

| Variant | Perplexity (95% CI) | Δ log-PPL vs. first sample (95% CI) |
|---|---|---|
| Unwatermarked, first sample | 93.1 [88.6,97.9] | +0.000 [+0.000,+0.000] |
| KGW | 82.4 [78.7,86.4] | -0.122 [-0.169,-0.075] |
| SynthID-Text | 106.3 [101.1,111.7] | +0.132 [+0.090,+0.173] |
| Truthprint (validated) | 85.1 [81.0,89.3] | -0.091 [-0.114,-0.068] |
