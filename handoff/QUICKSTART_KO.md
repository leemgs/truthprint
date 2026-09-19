# QUICKSTART — 복사/붙여넣기용 단계별 실행 가이드

> **🚀 터미널이 부담되면 Google Colab에서 셀만 실행하세요:**
> [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/leemgs/truthprint/blob/main/handoff/Truthprint_Handoff_Colab.ipynb)
> — `handoff/Truthprint_Handoff_Colab.ipynb`. 클론·설치·번역(무료 Google 번역)·주석 초안·
> 검증·zip 다운로드까지 셀 실행만으로 끝납니다. 아래는 로컬 터미널용 동일 절차입니다.

당신이 **직접 실행만 하면 되는** 순서입니다. 각 블록을 그대로 복사해 터미널에 붙여넣으세요.
(macOS/Linux 기준. Windows는 PowerShell에서 `python3`→`python`으로 바꾸세요.)

---

## STEP 0 — 저장소 받기 + 파이썬 준비

```bash
git clone https://github.com/leemgs/truthprint
cd truthprint
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade pip
cd code && python3 -m pip install -e ".[dev]" && cd ..
```

---

## STEP 1 — 내가 만든 것들이 실제로 돌아가는지 확인 (선택이지만 권장)

```bash
cd code
truthprint selftest          # P1–P4, L1–L3 => SELFTEST: PASS
truthprint challenge         # 필드별 typed=1.000 / no_mac=0.000 / embed≈0.01
pytest -q                    # 전체 테스트 통과
python scripts/eval_challenge.py   # paper/results/challenge_results.md 재생성
cd ..
```

---

## STEP 2 — 작업 폴더 만들기 (예제 복사)

```bash
cp -r handoff/samples my_handoff_data
ls my_handoff_data
```

이제 `my_handoff_data/` 안의 파일을 **실제 데이터로** 채웁니다.
`01_source_items.jsonl` 과 `split.json` 은 그대로 두세요(내가 제공).

---

## STEP 3 — 번역할 원문 문장 목록 뽑기

아래를 실행하면 번역해야 할 영어 문장이 `to_translate.csv` 로 저장됩니다.

```bash
python3 - <<'PY'
import json, csv
rows = []
with open("my_handoff_data/01_source_items.jsonl", encoding="utf-8") as fh:
    for line in fh:
        r = json.loads(line)
        for sid, text in r["watermarked_text"].items():
            rows.append((r["doc_id"], sid, text))
with open("my_handoff_data/to_translate.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["doc_id","sent_id","source_text"]); w.writerows(rows)
print(f"{len(rows)} sentences -> my_handoff_data/to_translate.csv")
for _, sid, t in rows: print(" ", sid, "|", t)
PY
```

---

## STEP 4 — 실제 번역기/패러프레이저로 변환하기  ⭐당신이 하는 핵심 작업

- `to_translate.csv` 의 `source_text` 를 **실제 시스템**(Google/DeepL/NLLB/GPT/Claude 등)으로
  번역·패러프레이즈·요약합니다.
- 그 결과를 `my_handoff_data/02_transformations.jsonl` 에 채웁니다.
  예제 파일의 형식을 그대로 쓰되 다음 두 가지를 **반드시** 바꾸세요:
  - `output_text` → 실제 변환 결과
  - `system` → 실제 사용한 시스템 이름+버전 (`REPLACE...` 문구가 남아 있으면 안 됨)
- 최소 언어쌍: EN→KO, EN→HI, KO→EN. 가능하면 round-trip / paraphrase / summary도.

형식 리마인더(한 줄에 JSON 하나):

```json
{"transform_id":"D0001-s1-ko","doc_id":"D0001","sent_id":"D0001-s1","transform_type":"translation","direction":"en->ko","system":"DeepL-2026.09","params":{},"output_text":"<실제 번역문>","round_trip":false}
```

---

## STEP 5 — 변환문을 사람이 주석하기  ⭐당신이 하는 핵심 작업

- 각 `transform_id` 에 대해 변환문을 읽고 `my_handoff_data/03_annotations.jsonl` 을 채웁니다.
- 채울 것: `invariants_observed`(6필드+agent/patient/predicate/quantity),
  `carriers_observed`(voice active/passive, time_position front/end, reliable true/false),
  `invariant_preserved`(의미 보존 여부). 필드 정의는 `handoff/schemas/SCHEMA_KO.md`.
- 가능하면 주석자 2명(`annotator_id` 다르게).

형식 리마인더:

```json
{"transform_id":"D0001-s1-ko","annotator_id":"A1","invariants_observed":{"agent":"the developer","patient":"server error","predicate":"FIX","quantity":1,"polarity":"positive","time_dir":"previous","modality":"asserted","attribution":"none","causation":"none"},"carriers_observed":[{"carrier":"voice","value":"active","reliable":true},{"carrier":"time_position","value":"end","reliable":false}],"invariant_preserved":true,"notes":""}
```

---

## STEP 6 — (권장) 사람 의미동일성 판단 / (선택) baseline 출력

```bash
# 04_human_factuality.csv : benign/altering 쌍의 human_equivalent(1/0) 채우기
# 05_baseline_outputs.jsonl : SynthID/SemStamp 등 공식 구현 검출 점수 (있으면)
```

둘 다 예제 형식을 그대로 따르면 됩니다. 어려우면 STEP 6은 건너뛰어도 됩니다.

---

## STEP 7 — 검증기로 형식 점검 (에러 0이 될 때까지 반복)

```bash
python3 handoff/validate_handoff.py my_handoff_data
```

- `RESULT: READY` 가 뜨면 완료.
- `PLACEHOLDER` 경고가 남아 있으면 STEP 4에서 `output_text`/`system` 을 아직 안 바꾼 것.
- `[ERROR]` 가 있으면 해당 줄을 고치고 다시 실행.

---

## STEP 8 — 나에게 전달

검증이 `READY` 가 되면, 이 세션에 이렇게 알려주세요:

```
my_handoff_data 채웠고 validate READY 떴어. 실측 실험 돌려서 논문 표 채워줘.
```

- 폴더를 커밋해서 푸시하거나(예: `git checkout -b data/handoff && cp -r my_handoff_data handoff/real_data && git add -A && git commit -m "add real handoff data" && git push -u origin data/handoff`),
  또는 파일을 첨부해 주세요.
- 그러면 제가: 실제 변환문에 대해 검출 실행 → held-out 보정 → TPR@{1,0.1,0.01}%FPR +
  bootstrap 95% CI → 필드별 지표·ValidRemoval·ablation → baseline 공정비교 →
  `paper/main.tex` 표/본문에 **실측 수치**로 반영(+acl 동기화)합니다.

---

## 자주 막히는 곳

- `pip install` 이 느리면 재시도하세요(네트워크). `-e "code/[dev]"` 는 repo 루트에서 실행.
- JSONL은 **한 줄=JSON 하나**. 쉼표로 잇거나 배열로 감싸지 마세요.
- `nonce_hex`/`key_id`/`message_bits` 는 절대 바꾸지 마세요(바꾸면 검출 실패).
- 작게 시작해도 됩니다: 언어쌍당 5~10문서로 파일럿 → 파이프라인 확인 후 규모 확대.
