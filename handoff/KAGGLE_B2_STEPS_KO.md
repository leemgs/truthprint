# Kaggle B2 실행 가이드 — 다국어(ZH/AR/DE 포함) 의미기반 실측

> **B2는 사람 주석이 필요 없습니다.** 의미 추출기가 번역문에서 불변량을 직접 복원하고
> 정답은 소스(`01`)에 있으므로, **소스 생성 → 번역 → eval 실행 → zip** 만 하면 됩니다.
> **바로 실행되는 노트북:** [`Truthprint_B2_Multilingual_Kaggle.ipynb`](Truthprint_B2_Multilingual_Kaggle.ipynb)
> — Kaggle: New Notebook → File → Import Notebook → Link 에
> `https://raw.githubusercontent.com/leemgs/truthprint/main/handoff/Truthprint_B2_Multilingual_Kaggle.ipynb`
> / Colab: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/leemgs/truthprint/blob/main/handoff/Truthprint_B2_Multilingual_Kaggle.ipynb)
>
> 아래는 동일 내용의 복사/붙여넣기 버전입니다. 새 노트북에 **순서대로 붙여넣고 실행**하세요.
> (Settings → **Internet: On**, Accelerator: None(CPU)로 충분. GPU 있으면 번역이 더 빠름.)

---

### 셀 1 — 저장소 클론 + 설치
```python
!rm -rf /kaggle/working/truthprint
!git clone -q https://github.com/leemgs/truthprint /kaggle/working/truthprint
!pip -q install -e /kaggle/working/truthprint/code
import sys, os
sys.path.insert(0, '/kaggle/working/truthprint/code')
os.chdir('/kaggle/working')
print('setup OK')
```

### 셀 2 — 실제-규모 영어 소스 생성 (문서 수 조절 가능)
```python
import os, json, random
from truthprint import challenge as ch
WORK = '/kaggle/working/b2_data'; os.makedirs(WORK, exist_ok=True)
N_DOCS, SENTS = 10, 16          # 문서 많을수록 CI가 좁아짐(시간↑). 첫 실행은 10 권장.
rng = random.Random(20260924)
rows = []
for d in range(N_DOCS):
    doc = f"D{d+1:04d}"; facts = [ch.sample_fact(rng) for _ in range(SENTS)]
    wm, fr = {}, []
    for i, f in enumerate(facts):
        sid = f"{doc}-s{i+1}"
        wm[sid] = ch.realize(f, 0, 0)                    # 영어 원문
        fr.append(dict(ch.ext_invariants(f), sent_id=sid))
    rows.append({"doc_id": doc, "lang_src": "en", "facts": fr, "watermarked_text": wm})
with open(f"{WORK}/01_source_items.jsonl", "w", encoding="utf-8") as fh:
    for r in rows: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"generated {N_DOCS} docs x {SENTS} sents")
```

### 셀 3 — NLLB로 5개 언어 + round-trip 번역 (실제 MT)
```python
import subprocess, sys, json
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
                'transformers', 'sentencepiece', 'torch'])
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
MODEL = 'facebook/nllb-200-distilled-600M'; SYSTEM = f'HuggingFace/{MODEL}'
TGT = ['ko', 'hi', 'zh', 'ar', 'de']
NLLB = {'en':'eng_Latn','ko':'kor_Hang','hi':'hin_Deva',
        'zh':'zho_Hans','ar':'arb_Arab','de':'deu_Latn'}
print('loading model (~2.4GB, first time only)...')
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL)
def tr(t, s, g):
    tok.src_lang = NLLB[s]; enc = tok(t, return_tensors='pt')
    bos = tok.convert_tokens_to_ids(NLLB[g])
    out = model.generate(**enc, forced_bos_token_id=bos, max_length=256)
    return tok.batch_decode(out, skip_special_tokens=True)[0]

rows = [json.loads(l) for l in open(f"{WORK}/01_source_items.jsonl", encoding="utf-8")]
tf = []
for r in rows:
    for sid, text in r["watermarked_text"].items():
        for lg in TGT:
            tf.append({"transform_id": f"{sid}-{lg}", "doc_id": r["doc_id"], "sent_id": sid,
                       "transform_type": "translation", "direction": f"en->{lg}",
                       "system": SYSTEM, "params": {}, "output_text": tr(text, 'en', lg),
                       "round_trip": False})
        rt = tr(tr(text, 'en', 'ko'), 'ko', 'en')
        tf.append({"transform_id": f"{sid}-rt", "doc_id": r["doc_id"], "sent_id": sid,
                   "transform_type": "roundtrip_translation", "direction": "en->ko->en",
                   "system": SYSTEM, "params": {}, "output_text": rt, "round_trip": True})
    print("translated", r["doc_id"])
with open(f"{WORK}/02_transformations.jsonl", "w", encoding="utf-8") as fh:
    for x in tf: fh.write(json.dumps(x, ensure_ascii=False) + "\n")
print("wrote", len(tf), "translations")
```

### 셀 4 — 실측 실행 (필드 복원 + 의미기반 provenance 인증)
```python
S = '/kaggle/working/truthprint/code/scripts'
!python {S}/eval_multilingual.py {WORK} --out {WORK}/stage2_multilingual.md
print("="*70)
!python {S}/eval_provenance.py  {WORK} --out {WORK}/provenance_realmt.md
```
- 위 두 표가 이 데이터의 **정직한 실측**입니다(ko/hi/zh/ar/de/round-trip 전 조건).

### 셀 5 — 결과 zip 만들기 → 나에게 전달
```python
import shutil
from IPython.display import FileLink
z = shutil.make_archive('/kaggle/working/b2_results', 'zip', WORK)
print('zip:', z)
FileLink('b2_results.zip')     # 이 링크 클릭해 다운로드 (또는 오른쪽 파일패널)
```

---

## 전달 후
`b2_results.zip`을 저에게 주시면, ZH/AR/DE 포함 **필드 복원율 + cross-lingual provenance
TPR/tamper 거부/FPR**을 논문 표에 실측으로 추가합니다.

## 팁 / 문제해결
- **인터넷 필수**(모델 다운로드). 없으면 셀 3에서 에러.
- 시간이 오래 걸리면 셀 2의 `N_DOCS`를 5로 줄여 먼저 파일럿.
- 셀 3 다운로드가 느린 건 최초 1회뿐. 같은 세션에서 재실행 시 캐시 사용.
- `stage2_multilingual.md` / `provenance_realmt.md` 를 열어 표를 미리 볼 수 있습니다:
  `print(open(f"{WORK}/provenance_realmt.md").read())`
