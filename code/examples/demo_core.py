"""Minimal core demo: encode a payload and detect it after erasures."""
from truthprint import Truthprint

tp = Truthprint(key=b"example-key-0123456789abcdef0123", msg_len=16, tag_bits=32)
invariants = {"events": [{"predicate": "FIX", "agent": "developer",
                          "patient": "server_error", "polarity": "positive"}]}
message = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1]
nonce = tp.new_nonce()

options = tp.encode(invariants, message, nonce)
# simulate a transformation that erases 30% of carriers
mask = [i % 10 < 3 for i in range(tp.n_carriers)]
result = tp.detect(invariants, options, nonce, erasure_mask=mask)

print("attributed:", result.attributed)
print("message recovered:", result.message == message)
print("reliable carriers:", result.reliable_carriers, "erasures:", result.erasures)
