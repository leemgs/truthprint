# Kaggle B2 실행 가이드 — 다국어(6개 언어) 의미기반 실측

> **B2는 사람 주석이 필요 없습니다.** 의미 추출기가 번역문에서 불변량을 직접 복원하고
> 정답은 소스(`01`)에 있으므로, **소스 생성 → 번역 → eval → zip** 만 하면 됩니다.
>
> **✅ 가장 쉬운 방법 — 노트북 Run All:**
> [`Truthprint_B2_Multilingual_Kaggle.ipynb`](Truthprint_B2_Multilingual_Kaggle.ipynb)
> — Kaggle: New Notebook → File → Import Notebook → Link 에
> `https://raw.githubusercontent.com/leemgs/truthprint/main/handoff/Truthprint_B2_Multilingual_Kaggle.ipynb`
> 붙여넣고 **Run All** → 마지막 셀에서 `b2_results.zip` 다운로드 → 저에게 전달.
>
> **설정(오른쪽 패널):** Settings → **Internet: On**, Accelerator → **GPU T4 x2**(권장,
> 없으면 CPU도 가능). 기본 `N_DOCS=50`이면 GPU에서 대략 5~10분입니다.

---

아래는 노트북과 **동일 내용의 복사/붙여넣기 버전**입니다. 새 노트북에 순서대로 붙여넣고
실행하세요.

### 셀 1 — 환경 감지 + 클론 + 설치
```python
import os, sys, subprocess
BASE = '/kaggle/working' if os.path.isdir('/kaggle/working') else (
        '/content' if os.path.isdir('/content') else os.getcwd())
REPO = os.path.join(BASE, 'truthprint')
if not os.path.isdir(REPO):
    r = subprocess.run(['git','clone','--depth','1',
                        'https://github.com/leemgs/truthprint', REPO])
    if r.returncode != 0:
        raise RuntimeError('git clone 실패 -> 인터넷(Internet: On)을 확인하세요.')
subprocess.run([sys.executable,'-m','pip','install','-q','-e', os.path.join(REPO,'code')])
sys.path.insert(0, os.path.join(REPO,'code'))
WORK = os.path.join(BASE, 'b2_data'); os.makedirs(WORK, exist_ok=True)
SCRIPTS = os.path.join(REPO,'code','scripts')
print('BASE =', BASE); print('WORK =', WORK); print('setup OK')
```

### 셀 2 — 실제-규모 영어 소스 생성
```python
import json, random
from truthprint import challenge as ch
N_DOCS, SENTS = 50, 16     # 문서↑ = 신뢰구간(CI)↑. 50 권장. 빠른 파일럿은 10.
rng = random.Random(20260924); rows = []
for d in range(N_DOCS):
    doc = f'D{d+1:04d}'; facts = [ch.sample_fact(rng) for _ in range(SENTS)]
    wm, fr = {}, []
    for i, f in enumerate(facts):
        sid = f'{doc}-s{i+1}'; wm[sid] = ch.realize(f, 0, 0)
        fr.append(dict(ch.ext_invariants(f), sent_id=sid))
    rows.append({'doc_id': doc, 'lang_src': 'en', 'facts': fr, 'watermarked_text': wm})
with open(os.path.join(WORK,'01_source_items.jsonl'),'w',encoding='utf-8') as fh:
    for r in rows: fh.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'generated {N_DOCS} docs x {SENTS} sents')
```

### 셀 3 — NLLB로 5개 언어 + round-trip 번역 (GPU 자동 / 배치)
```python
import subprocess, sys, json, torch
subprocess.run([sys.executable,'-m','pip','install','-q','transformers','sentencepiece'])
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
MODEL = 'facebook/nllb-200-distilled-600M'; SYSTEM = f'HuggingFace/{MODEL}'
TGT = ['ko','hi','zh','ar','de']
NLLB = {'en':'eng_Latn','ko':'kor_Hang','hi':'hin_Deva',
        'zh':'zho_Hans','ar':'arb_Arab','de':'deu_Latn'}
DEV = 'cuda' if torch.cuda.is_available() else 'cpu'
print('device:', DEV, '| loading model (~2.4GB, first time only)...')
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL).to(DEV).eval()
BATCH = 32   # GPU면 그대로, CPU 메모리 부족 시 8로 낮추세요.
def tr_batch(texts, s, g):
    tok.src_lang = NLLB[s]; bos = tok.convert_tokens_to_ids(NLLB[g]); out = []
    for i in range(0, len(texts), BATCH):
        chunk = texts[i:i+BATCH]
        enc = tok(chunk, return_tensors='pt', padding=True, truncation=True,
                  max_length=256).to(DEV)
        with torch.no_grad():
            o = model.generate(**enc, forced_bos_token_id=bos, max_length=256)
        out.extend(tok.batch_decode(o, skip_special_tokens=True))
        print(f'  {s}->{g}  {min(i+BATCH,len(texts))}/{len(texts)}')
    return out
rows = [json.loads(l) for l in open(os.path.join(WORK,'01_source_items.jsonl'),encoding='utf-8')]
items = [(r['doc_id'], sid, txt) for r in rows for sid, txt in r['watermarked_text'].items()]
srcs = [t for _,_,t in items]
print(f'translating {len(srcs)} sentences x ({len(TGT)} langs + round-trip)')
tf = []
for lg in TGT:
    outs = tr_batch(srcs, 'en', lg)
    for (doc, sid, _), o in zip(items, outs):
        tf.append({'transform_id':f'{sid}-{lg}','doc_id':doc,'sent_id':sid,
                   'transform_type':'translation','direction':f'en->{lg}','system':SYSTEM,
                   'params':{},'output_text':o,'round_trip':False})
ko_mid = tr_batch(srcs, 'en', 'ko'); back = tr_batch(ko_mid, 'ko', 'en')   # round-trip
for (doc, sid, _), o in zip(items, back):
    tf.append({'transform_id':f'{sid}-rt','doc_id':doc,'sent_id':sid,
               'transform_type':'roundtrip_translation','direction':'en->ko->en','system':SYSTEM,
               'params':{},'output_text':o,'round_trip':True})
with open(os.path.join(WORK,'02_transformations.jsonl'),'w',encoding='utf-8') as fh:
    for x in tf: fh.write(json.dumps(x, ensure_ascii=False) + '\n')
print('wrote', len(tf), 'translations')
```

### 셀 4 — 실측 실행 (필드 복원율 + 의미기반 provenance 인증)
```python
import subprocess, sys, os
for name in ['eval_multilingual.py','eval_provenance.py']:
    print('='*72); print('RUN', name); print('='*72)
    out = os.path.join(WORK, name.replace('eval_','').replace('.py','')+'.md')
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS,name), WORK, '--out', out],
                       capture_output=True, text=True)
    print(r.stdout or r.stderr)
```

### 셀 5 — 결과 zip 만들기 → 나에게 전달
```python
import shutil, os
zip_path = shutil.make_archive(os.path.join(BASE,'b2_results'), 'zip', WORK)
print('created:', zip_path)
downloaded = False
try:
    from google.colab import files; files.download(zip_path); downloaded = True
except Exception:
    pass
if not downloaded:
    try:
        from IPython.display import FileLink, display
        print('아래 링크 클릭해 다운로드:'); display(FileLink(os.path.relpath(zip_path, os.getcwd())))
    except Exception:
        print('수동 다운로드 경로:', zip_path)
    print('Kaggle이면 오른쪽 파일 패널에서 b2_results.zip 우클릭 -> Download 도 가능합니다.')
```

---

## 전달 후
`b2_results.zip`을 저에게 주시면, 6개 언어 **필드 복원율 + cross-lingual provenance
TPR/tamper 거부/FPR**을 **더 좁은 신뢰구간**으로 논문 표에 갱신합니다.

## 팁 / 문제해결
- **인터넷 필수**(모델 다운로드). 없으면 셀 3에서 에러.
- **속도**: GPU(T4)면 50문서(4,800문장)가 대략 5~10분. CPU면 훨씬 오래 걸리니 `N_DOCS`를
  20으로 낮추거나 `BATCH`를 8로 조정하세요.
- 셀 3 다운로드가 느린 건 최초 1회뿐. 같은 세션 재실행 시 캐시 사용.
- 표를 미리 보려면: `print(open(f"{WORK}/multilingual.md").read())`,
  `print(open(f"{WORK}/provenance_realmt.md").read())`
