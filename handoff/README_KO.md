# Truthprint 실증 실험 데이터 핸드오프 키트 (사용자 ⇄ Claude)

> **이 폴더의 목적:** ACL main track이 요구하는 "실제 다국어 end-to-end 실험"을
> 채우려면, 이 원격 환경에서 **실행 불가능한 부분(실제 기계번역·실제 LLM 생성·사람
> 주석·사람 판단)** 을 당신이 직접 만들어서 주셔야 합니다. 이 문서는 **당신이 무엇을,
> 어떤 형식으로 만들어 주면 되는지**를 헷갈리지 않게 예제 샘플과 함께 정리한 것입니다.
>
> 형식만 맞춰서 `handoff/` 폴더를 채워 주시면, 나머지(코덱 실행, 검출, 통계, 표 채우기,
> 논문 반영)는 제가 합니다.

---

## 0. 역할 분담 한눈에 보기

| 단계 | 누가 | 이 환경에서 가능? |
|---|---|---|
| 실제 기계번역 / 패러프레이즈 / 요약 출력 생성 | **당신** | ❌ (API·네트워크·GPU 필요) |
| 변환된 문장의 사람 gold 주석(불변량·carrier) | **당신** | ❌ (사람 판단) |
| 사람 factual-equivalence 판단 | **당신** | ❌ (사람 판단) |
| 공식 baseline(SynthID/SemStamp/SWAN 등) 검출 출력 | **당신**(선택) | ❌ (원 구현·모델 필요) |
| Truthprint 인코드/검출, ECC, MAC 실행 | Claude | ✅ |
| held-out 보정, TPR@FPR, bootstrap 신뢰구간 | Claude | ✅ |
| 필드별 지표·ValidRemoval·ablation 계산 | Claude | ✅ |
| 논문 표/그림/본문 반영 | Claude | ✅ |

핵심: **당신은 "실제 세상에서만 나오는 데이터"만 채우면 됩니다.** 계산·집계·작성은 제 몫입니다.

---

## 1. 당신이 채워야 할 파일 (우선순위 순)

각 파일의 **정식 예제**는 `handoff/samples/`에 있습니다. 스키마(필수 필드 정의)는
[`handoff/schemas/SCHEMA_KO.md`](schemas/SCHEMA_KO.md)에 있습니다. 예제 파일을 복사해
내용만 실제 데이터로 바꾸는 방식이 가장 안전합니다.

### ⭐ 필수 (이것만 있으면 최소 실측 실험 성립)

1. **`02_transformations.jsonl`** — *가장 중요.*
   원문 문장을 **실제 번역기/패러프레이저**로 변환한 결과.
   - 예: EN→KO, EN→HI, KO→EN, round-trip, paraphrase, summary.
   - `system` 필드에 실제 사용한 시스템 이름·버전을 반드시 기입(재현성).
   - 원문(`01_source_items.jsonl`)은 제가 제공합니다. 당신은 그 원문들을 번역만 하면 됩니다.

2. **`03_annotations.jsonl`** — *두 번째로 중요(= 논문의 "frontend").*
   변환된 각 문장을 사람이 읽고, **불변량 필드**(극성·수량·시간방향·양태·귀속·인과)와
   **carrier 관측**(태 active/passive, 시간구 위치 front/end, 신뢰 여부)을 주석.
   - 이게 있으면 저는 실제 번역문에 대해 검출을 **진짜로** 돌려 TPR/복구율을 냅니다.
   - 최소 2명 주석 + 불일치율 보고 권장(annotator_id로 구분).

### ○ 권장 (지표 품질·설득력 상승)

3. **`04_human_factuality.csv`** — benign(의미보존) vs altering(의미변경) 쌍에 대한
   사람의 "의미 동일?" 판단. RQ1(semantic fidelity)과 ValidRemoval 평가에 사용.

4. **`05_baseline_outputs.jsonl`** — 공식/검증된 baseline 검출기 출력(가능하면).
   SynthID-Text, SemStamp, SWAN, DEW 등을 **동일 원문·동일 변환**에 돌린 점수·판정.
   - 어려우면 생략 가능. 대신 저는 "공정 비교는 향후 과제"로 정직하게 표기합니다.

### ◇ 제가 제공/생성 (당신은 건드릴 필요 없음)

- **`01_source_items.jsonl`** — 워터마킹된 원문(내가 코덱으로 생성). 당신은 이걸
  **번역만** 하면 됩니다. (직접 만든 실제 뉴스/위키 문장을 쓰고 싶으면 교체 가능.)
- **`split.json`** — calibration/test 문서 분할(내가 관리, 당신이 바꿔도 됨).

---

## 2. 지금 바로 할 일 (체크리스트)

- [ ] `handoff/samples/`의 예제들을 열어 형식을 확인한다.
- [ ] `01_source_items.jsonl`의 `watermarked_text` 문장들을 **실제 번역기**로 번역/
      패러프레이즈해 `02_transformations.jsonl`을 채운다. (`system` 이름 꼭 기입)
- [ ] 변환된 각 문장을 사람이 주석해 `03_annotations.jsonl`을 채운다.
- [ ] (권장) `04_human_factuality.csv`, `05_baseline_outputs.jsonl`을 채운다.
- [ ] 검증기를 돌린다: `python3 handoff/validate_handoff.py handoff/samples`
      → 당신 데이터 폴더로 바꿔 실행. **모두 OK가 뜨면 저에게 폴더를 주세요.**
- [ ] 저에게 "handoff 채웠다"고 알려주시면, 제가 실측 실험을 돌리고 논문 표를 채웁니다.

---

## 3. 규모 가이드 (ACL main track 기준 최소치)

| 축 | 최소 권장 |
|---|---|
| 언어쌍 | EN→KO, EN→HI, KO→EN (최소 3), 가능하면 ZH/AR 추가 |
| 도메인 | 뉴스·위키형 설명·기술문서 (최소 3) |
| 문서 수 | 도메인·언어쌍당 50+ 문서 (총 500+ 문서면 CI가 탄탄) |
| 변환 종류 | 직접번역·round-trip·paraphrase(강도 2~3)·summary(압축 25/50%) |
| 주석자 | 문장당 2명 + 불일치(κ) 보고 |
| baseline | 최소 SynthID + SemStamp (원 구현) |

*소규모(예: 언어쌍당 10문서)라도 파일럿으로 먼저 주시면, 파이프라인을 검증하고
실제 수치를 낸 뒤 규모를 키우는 방식으로 진행할 수 있습니다.*

---

## 4. 형식 규칙 (공통)

- 모든 `.jsonl`은 **한 줄에 JSON 객체 하나**(UTF-8). 쉼표로 잇지 마세요.
- `.csv`는 첫 줄이 헤더. 값에 쉼표가 있으면 큰따옴표로 감싸세요.
- ID 규칙: `doc_id`는 문서, `sent_id = "<doc_id>-s<N>"`, `transform_id`는 변환 1건당 고유.
- `nonce_hex`, `key_id`, `message_bits` 등 암호 관련 필드는 **제가 넣은 값을 그대로 유지**
  하세요(바꾸면 검출이 실패합니다).
- 모르는 필드는 비우지 말고 스키마의 허용값(enum)에서 고르세요. 애매하면 `notes`에 설명.

---

## 5. 검증기 사용법

```bash
# 예제로 먼저 통과 확인
python3 handoff/validate_handoff.py handoff/samples

# 당신의 실제 데이터 폴더로
python3 handoff/validate_handoff.py /path/to/your/handoff_data
```

검증기는 필수 필드·enum·상호참조(transform이 존재하는 source를 가리키는지 등)를
확인하고 **준비도 리포트**를 출력합니다. 오류가 0이면 저에게 넘기시면 됩니다.

---

## 6. 제가 데이터를 받은 뒤 하는 일 (참고)

1. `02`+`03`을 코덱에 연결해 **실제 변환문**에 대해 인코드→검출 end-to-end 실행.
2. held-out `split.json`으로 임계값 보정 → TPR@{1,0.1,0.01}%FPR + bootstrap 95% CI.
3. 필드별 불변량 precision/recall·consistency, ValidRemoval(제거∧의미보존) 계산.
4. ablation(full / no-MAC / no-ECC / embedding-only) 실측 표.
5. `05` baseline과 동일 operating point에서 공정 비교.
6. 논문 `main.tex` 표/그림/본문에 **실측 수치**로 반영하고 acl 소스 동기화.

> 저는 당신이 준 실제 수치만 사용하며, 시뮬레이션 값을 실제 결과로 둔갑시키지 않습니다.
> 부족한 축은 "미확보"로 정직하게 남깁니다.
