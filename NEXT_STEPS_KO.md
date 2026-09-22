# 다음 단계 — 저자가 꼭 해야 하는 최소 작업 + 연구 윤리 체크리스트

> 이 문서는 Claude가 **자율적으로 완료한 작업**과, 성격상 **저자(사람)만 할 수 있는 최소
> 작업** 및 **연구 윤리 항목**을 분리해 정리한 것입니다. 손이 덜 가도록, 남은 각 항목에
> 실행 명령·위치·이유를 함께 적었습니다.

---

## A. Claude가 이미 자율 완료한 것 (실측·재현 가능, `main` 병합됨)

| 결과 | 수치(실측) | 위치 |
|---|---|---|
| 암호·코딩 코어 P1–P4 | 위양성 0/20k, per-test 2⁻³² | `paper/reference/`, `code/` |
| 필드별 challenge ablation C1–C3 | typed tamper 1.000 / no-MAC 0.000 / embedding 0.012 (CI 포함) | `paper/results/challenge_results.md` |
| real-MT 파일럿 (표면 carrier) | 파서 커버리지 **0/192** (정직한 음의 결과) | `paper/results/realmt_pilot.md` |
| **Stage-2 다국어 불변량 추출기** | 실제 NLLB 192건에서 필드 복원 **0.89–1.00** | `paper/results/stage2_multilingual.md` |
| **의미기반 provenance 인증** | 문서 귀속 **1.000** (KO/HI/round-trip), 문장 TPR 0.80–0.95, tamper 거부 ≥0.98, FPR~0 | `paper/results/provenance_realmt.md` |
| 리뷰·원고 정직성 정비 | 초록·Claim–Evidence 표·윤리 절에 실측 반영, acl 동기화 | `paper/main.tex`, `paper/acl_main.tex` |

재현: `cd code && pip install -e ".[dev]" && pytest -q && truthprint selftest`.
새 스크립트: `scripts/eval_multilingual.py`, `scripts/eval_provenance.py`,
`scripts/eval_handoff.py --objective`.

---

## B. 저자만 할 수 있는 최소 작업 (main-track 경쟁력 강화)

우선순위 순. 각 항목은 **왜 필요한지 + 정확히 무엇을 하면 되는지**를 적었습니다.

### B1. CI 강화용 데이터 규모 확대 ⭐ (가장 효과 큼)
- **왜:** 현재 문서 4개라 문서-단위 귀속 CI가 [0.51, 1.00]로 넓습니다. 문서 수를 늘리면
  같은 파이프라인으로 CI가 좁혀집니다(수치 조작 아님, 표본만 증가).
- **어떻게:** Kaggle 노트북 STEP 2에서 `N_DOCS=30`, `SENTS_PER_DOC=16`로 올리고
  STEP 3 → **STEP 4B(로컬 NLLB)** → STEP 5 → STEP 5B → STEP 7 → STEP 7B → STEP 8 실행 후
  zip 전달. (번역·주석 초안은 노트북이 자동 처리, 사람은 STEP 5 검토만.)
- Claude가 받으면 `eval_multilingual.py`/`eval_provenance.py`로 재측정해 CI를 갱신합니다.

### B2. 언어 축 확대 (ZH/AR/DE 등)
- **왜:** "다국어" 주장을 3개 언어쌍 이상으로 뒷받침(리뷰 W1/W7).
- **어떻게:** 노트북 STEP 4B의 NLLB 타깃 언어 코드에 `zho_Hans`, `arb_Arab`, `deu_Latn`
  등을 추가(코드 한 줄). Claude가 원하면 그 셀 변형을 만들어 드립니다. 새 언어는
  `multilingual.py`에 해당 언어 lexicon 추가가 필요 → Claude가 작성 가능(요청만).

### B3. 사람 factual-equivalence 주석 (RQ1 / ValidRemoval)
- **왜:** "의미 보존" 판단을 사람 기준으로 검증(리뷰 W1). 자동 판단만으론 부족.
- **어떻게:** `handoff/samples/04_human_factuality.csv` 형식대로 benign/altering 쌍에
  `human_equivalent`(0/1)를 사람 2명이 채움. Claude가 κ(일치도)와 ValidRemoval을 계산.

### B4. 공식 baseline 비교 (리뷰 W3)
- **왜:** SynthID/SemStamp 등과 동일 조건 비교가 있어야 우열 주장 가능.
- **어떻게:** 공식 구현을 동일 원문·번역에 돌려 `05_baseline_outputs.jsonl` 채움.
  (GPU/모델 필요 → 저자 환경에서.) Claude가 동일 operating point 비교 표를 생성.

### B5. (선택) 실제 LLM 생성물로 확대
- 현재 원문은 템플릿 사실. 실제 LLM 생성 문장으로 `01`을 교체하면 외적 타당성↑.
  단, 그러면 폐쇄도메인 파서 밖이라 wide-coverage parser(아래 C 항목)가 선행돼야 함.

---

## C. Claude가 이어서 할 수 있는 것 (요청 시, 사람 데이터 없이도 일부 가능)
- **경량 neural/광역 파서**로 `multilingual.py` 확장(현재는 lexicon 규칙). 단, 이 환경엔
  GPU·모델 다운로드 제약이 있어, 저자 환경(Colab/Kaggle GPU)에서 돌릴 학습·평가 노트북을
  Claude가 작성해 드리는 형태가 현실적입니다.
- **W6 원고 재구성**(roadmap·software architecture·진단 시뮬레이션 표를 appendix로 이동해
  ACL 8쪽 본문 예산 맞춤). LaTeX 컴파일러가 이 환경엔 없어, Claude가 편집안을 만들고
  저자가 로컬에서 `make acl`로 컴파일 확인하는 방식을 권장.

---

## D. 연구 윤리 — 저자가 직접 확인·서명해야 하는 항목 (Claude가 대신 못 함)

이들은 **권한·판단·신원**이 필요해 반드시 저자가 수행합니다.

1. **ACL/ARR Responsible NLP Checklist**: 제출 시스템에서 저자가 직접 체크. 본 원고의
   Limitations·Ethics 절은 이미 초안이 있으나, 체크리스트 문항 응답은 저자 책임.
2. **데이터 라이선스·동의**: 평가 텍스트(실제 LLM/뉴스/위키 등)를 쓸 경우 라이선스/동의
   확보. 현재 파일럿은 합성 템플릿 사실이라 해당 없음.
3. **인간 주석 보상·문서화**: B3/B4에서 사람 주석을 쓰면 보상·가이드라인·IRB 해당 여부를
   문서화.
4. **이중용도(dual-use) 진술**: provenance 검출기의 오·남용(허위 귀속, 검열, 자동 징계)
   위험과 완화책. 원고 Ethics 절에 초안 있음 — 저자가 배포 맥락에 맞게 최종 확정.
5. **키·nonce·ledger 거버넌스**: 실제 배포 시 키 회전·접근통제·감사 정책은 저자/기관의
   운영 책임.
6. **저자 신원·이해상충·자금출처**: 익명 심사본에는 넣지 않되, camera-ready에서 저자가
   기입. (현재 `acl_main.tex`는 익명 유지 — `make check`가 신원 누출을 차단.)
7. **AI 보조 사용 고지**: 본 연구의 코드·원고 정비에 AI(클로드) 보조가 사용되었음을
   투고 규정에 맞게 저자가 고지.

---

## E. 한 줄 요약
- **Claude 자율 완료:** 코어 검증 + 오프라인 ablation + real-MT 음의 결과 + **Stage-2/
  provenance 양의 실측** + 원고 정직 반영(모두 `main`).
- **저자 최소 작업:** (B1) 문서 수 늘려 CI 강화가 가장 효과적, 나머지 B2–B5는 여력에 따라.
- **윤리:** D의 7개 항목은 저자 서명·판단 필요.
