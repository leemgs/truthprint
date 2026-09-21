"""End-to-end test of the handoff consumer (scripts/eval_handoff.py).

Builds a complete, READY synthetic handoff folder (large enough that the code
has capacity margin), then asserts that the consumer:
  * attributes and exactly recovers the payload for a benign condition whose
    carriers survive and whose invariants are preserved, and
  * does NOT attribute a meaning-altering (tamper) condition.
This proves the consumer is correct, independent of any real translation data.
"""
import importlib.util
import json
import random
from pathlib import Path

from truthprint import challenge as ch
from truthprint.core import Truthprint

KEY = b"truthprint-challenge-key-01234567"[:32]
_VOICE = {0: "active", 1: "passive"}
_TIMEPOS = {0: "front", 1: "end"}


def _load_eval_handoff():
    path = Path(__file__).resolve().parent.parent / "scripts" / "eval_handoff.py"
    spec = importlib.util.spec_from_file_location("eval_handoff", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build_handoff(tmp: Path, n_sent=16, msg_len=8, tag_bits=16):
    rng = random.Random(2027)
    facts = [ch.sample_fact(rng) for _ in range(n_sent)]
    core = Truthprint(KEY, msg_len=msg_len, tag_bits=tag_bits, code_n=2 * n_sent)
    msg = [rng.randrange(2) for _ in range(msg_len)]
    nonce = bytes(rng.randrange(256) for _ in range(12))
    options = core.encode(ch.doc_invariants(facts), msg, nonce)

    doc_id = "D0001"
    wm = {f"{doc_id}-s{i+1}": ch.realize(facts[i], options[2*i], options[2*i+1])
          for i in range(n_sent)}
    src = {"doc_id": doc_id, "split": "test", "lang_src": "en", "domain": "news",
           "scheme": "truthprint", "key_id": "k1", "nonce_hex": nonce.hex(),
           "message_bits": "".join(map(str, msg)),
           "code": {"n": 2*n_sent, "k": msg_len+tag_bits,
                    "msg_len": msg_len, "tag_bits": tag_bits},
           "facts": [dict(ch.ext_invariants(facts[i]), sent_id=f"{doc_id}-s{i+1}")
                     for i in range(n_sent)],
           "watermarked_text": wm}
    (tmp / "01_source_items.jsonl").write_text(
        json.dumps(src, ensure_ascii=False) + "\n", encoding="utf-8")

    transforms, annotations = [], []
    for i in range(n_sent):
        sid = f"{doc_id}-s{i+1}"
        v, t = options[2*i], options[2*i+1]
        inv = ch.ext_invariants(facts[i])
        # benign condition "-ok": carriers preserved & reliable, meaning kept
        transforms.append({"transform_id": f"{sid}-ok", "doc_id": doc_id,
                           "sent_id": sid, "transform_type": "paraphrase",
                           "direction": "en->en", "system": "TEST",
                           "params": {}, "output_text": wm[sid],
                           "round_trip": False})
        annotations.append({"transform_id": f"{sid}-ok", "annotator_id": "T",
                            "invariants_observed": dict(inv),
                            "carriers_observed": [
                                {"carrier": "voice", "value": _VOICE[v],
                                 "reliable": True},
                                {"carrier": "time_position", "value": _TIMEPOS[t],
                                 "reliable": True}],
                            "invariant_preserved": True, "notes": ""})
        # tamper condition "-adv": polarity flipped (meaning altered)
        inv2 = dict(inv)
        inv2["polarity"] = "negative" if inv["polarity"] == "positive" else "positive"
        transforms.append({"transform_id": f"{sid}-adv", "doc_id": doc_id,
                           "sent_id": sid, "transform_type": "adaptive_paraphrase",
                           "direction": "en->en", "system": "TEST",
                           "params": {}, "output_text": wm[sid],
                           "round_trip": False})
        annotations.append({"transform_id": f"{sid}-adv", "annotator_id": "T",
                            "invariants_observed": inv2,
                            "carriers_observed": [
                                {"carrier": "voice", "value": _VOICE[v],
                                 "reliable": True},
                                {"carrier": "time_position", "value": _TIMEPOS[t],
                                 "reliable": True}],
                            "invariant_preserved": False, "notes": "polarity flip"})

    with (tmp / "02_transformations.jsonl").open("w", encoding="utf-8") as fh:
        for r in transforms:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (tmp / "03_annotations.jsonl").open("w", encoding="utf-8") as fh:
        for r in annotations:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (tmp / "split.json").write_text(json.dumps({"calibration": [], "test": [doc_id]}),
                                    encoding="utf-8")
    return msg


def test_handoff_consumer_benign_and_tamper(tmp_path):
    _build_handoff(tmp_path)
    mod = _load_eval_handoff()
    res = mod.evaluate(str(tmp_path), key=KEY)
    assert "error" not in res, res
    ok = res["conditions"]["ok"]
    adv = res["conditions"]["adv"]
    # benign: attributed and exactly recovered
    assert ok["evaluable_docs"] == 1
    assert ok["attribution_rate"][0] == 1.0
    assert ok["exact_recovery_rate"][0] == 1.0
    # tamper: not attributed
    assert adv["evaluable_docs"] == 1
    assert adv["attribution_rate"][0] == 0.0


def test_handoff_consumer_reports_error_on_empty(tmp_path):
    (tmp_path / "01_source_items.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "02_transformations.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "03_annotations.jsonl").write_text("", encoding="utf-8")
    mod = _load_eval_handoff()
    res = mod.evaluate(str(tmp_path), key=KEY)
    assert "error" in res
