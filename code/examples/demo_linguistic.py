"""Linguistic demo: watermark real sentences, transform them, then detect."""
import random
from truthprint.linguistic import (Fact, LinguisticCodec,
                                   invariant_preserving_transform)

rng = random.Random(0)
# 32 sentences -> 64 carriers; with an 8-bit message + 16-bit tag (k=24) the
# code rate is ~0.375, so recovery is robust well past the ~20% erasure below.
facts = [Fact("the developer", "the server error"),
         Fact("the auditor", "the data leak")] * 16  # 32 sentences
codec = LinguisticCodec(b"example-key-0123456789abcdef0123",
                        n_sentences=len(facts), msg_len=8, tag_bits=16)
msg = [rng.randint(0, 1) for _ in range(8)]
nonce = codec.core.new_nonce()

sentences = codec.encode(facts, msg, nonce)
print("first watermarked sentence:\n  ", sentences[0])

transformed, reliability = [], []
for s in sentences:
    s2, rel = invariant_preserving_transform(s, rng, 0.20)
    transformed.append(s2)
    reliability.append(rel)

result = codec.detect(transformed, nonce, reliability)
print("attributed after transform:", result.attributed,
      "| message recovered:", result.message == msg)
