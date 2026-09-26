# W4 baseline 비교 — 데이터 스키마

주 트랙 리뷰 W4("공식 baseline과 동일 조건 실데이터 비교")를 위한 산출물 스키마입니다.
노트북 `Truthprint_W4_Baselines_Kaggle.ipynb`가 아래 파일을 생성하고,
`code/scripts/eval_baselines_real.py`가 이를 채점합니다.

## `05_baseline_outputs.jsonl`

한 줄 = 한 (method, 문서, 조건, watermarked?) 레코드. 필수 필드:

| 필드 | 타입 | 의미 |
|---|---|---|
| `method` | str | 검출기 이름 (예: `KGW`, `SynthID`, `SIR`, `SemStamp`) |
| `impl` | str | 정확한 구현·모델·하이퍼파라미터 (재현용). 예: `MarkLLM SynthID, LLM=gpt2` |
| `doc_id` | str | 문서 식별자 (Truthprint 소스와 동일) |
| `condition` | str | `clean` \| `rt`(round-trip) \| `ko` \| `hi` \| `zh` \| `ar` \| `de` |
| `watermarked` | bool | `true`=양성(워터마크됨), `false`=null(비워터마크) — **FPR 보정에 필수** |
| `score` | float | 검출기 점수 (높을수록 워터마크. z-score 등) |
| `payload_ok` | bool/null | (선택) 다중비트 방식에서 페이로드 정확 복원 여부, 없으면 `null` |

### 핵심 규칙 (과학적 정직성)
1. **동일 파이프라인:** 모든 method가 **같은 소스 내용**을 워터마크하고, **같은 실제 NLLB
   번역**(6개 조건)을 거친 뒤, **자기 검출기**로 판정. 이것이 apples-to-apples의 조건.
2. **null 필수:** 각 method는 `watermarked=false` 레코드(비워터마크 생성물의 점수)를
   반드시 포함해야 함. 채점기가 이 분포에서 1% FPR 임계를 보정함.
3. **조건 코드**는 위 7종만 사용. Truthprint 실행과 동일한 언어 축.

## 채점기 사용
```bash
python3 code/scripts/eval_baselines_real.py 05_baseline_outputs.jsonl \
    --truthprint paper/results/provenance_realmt.json --fpr 0.01 --out paper/results
```
출력: `baselines_real.{json,md}` — method×조건 TPR@1%FPR(Wilson CI) + ROC-AUC(bootstrap CI),
그리고 Truthprint 의미기반 provenance 수치를 같은 표에 병합.

## 최소 vs 권장
- **최소(보장):** 자체 완결형 KGW(실제 LLM+실제 z-score) 한 개 — MarkLLM 없이도 실제
  토큰-레벨 baseline 수치가 나옴. He et al.(2024)이 예측한 "번역 후 붕괴"를 실측.
- **권장:** MarkLLM로 SynthID·SIR 추가(노트북 Cell 5의 선택 블록). 버전에 따라 API가
  다를 수 있어 try/except로 감쌌음 — 실패해도 KGW 결과는 남음.
- **선택:** SemStamp/SWAN 등은 공식 repo가 있으면 같은 스키마로 추가.
