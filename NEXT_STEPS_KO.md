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
| **Stage-2 다국어 불변량 추출기 (6개 언어 완료)** | 실제 NLLB **960건**(EN-RT + KO/HI/ZH/AR/DE)에서 필드 복원 **0.90–1.00** (모든 필드 ≥0.90) | `paper/results/stage2_multilingual.md` |
| **의미기반 provenance 인증 (6개 언어)** | 문서 귀속 6개 중 5개 **1.000**(AR 0.900), 문장 TPR 5개 언어 ≥0.93 (AR 0.656), tamper 거부 ≥0.99, FPR≤0.013 | `paper/results/provenance_realmt.md` |
| 리뷰·원고 정직성 정비 | 초록·Claim–Evidence 표·Stage-2/provenance 절·윤리 절에 6개 언어 실측 반영, acl 동기화 | `paper/main.tex`, `paper/acl_main.tex` |

재현: `cd code && pip install -e ".[dev]" && pytest -q && truthprint selftest`.
새 스크립트: `scripts/eval_multilingual.py`, `scripts/eval_provenance.py`,
`scripts/eval_handoff.py --objective`.

---

## B. 저자만 할 수 있는 최소 작업 (main-track 경쟁력 강화)

우선순위 순. 각 항목은 **왜 필요한지 + 정확히 무엇을 하면 되는지**를 적었습니다.

### B1. CI 강화용 데이터 규모 확대 ⭐ (지금 남은 유일한 필수 작업, 가장 효과 큼)
- **왜:** 현재 문서 10개라 문서-단위 귀속 CI가 여전히 넓습니다([0.722, 1.000]).
  문서 수를 늘리면 **같은 파이프라인으로 CI만 좁혀집니다**(수치 조작 아님, 표본만 증가).
- **어떻게 (제일 쉬움):** `handoff/Truthprint_B2_Multilingual_Kaggle.ipynb`를 Kaggle에서
  열고 (Settings → Internet: On, Accelerator: **GPU T4**) **Run All** →
  마지막 셀에서 `b2_results.zip` 다운로드 → 저에게 전달. 기본 `N_DOCS=50`입니다.
  복사/붙여넣기 절차는 `handoff/KAGGLE_B2_STEPS_KO.md` 참고.
- Claude가 받으면 `eval_multilingual.py`/`eval_provenance.py`로 재측정해 CI를 갱신합니다.

### B2. 언어 축 확대 (ZH/AR/DE) — ✅ 완료
- 6개 언어(EN round-trip + KO/HI/ZH/AR/DE) lexicon 구축·실측 완료. 아랍어 약점(개체
  번역 편차)까지 정직하게 진단·보고됨. **추가로 언어를 더 넣고 싶으면** 노트북 셀 3의
  `TGT`/`NLLB`에 언어 코드를 추가하고 요청 주세요(해당 lexicon은 제가 작성).

### B3. 사람 factual-equivalence 주석 (RQ1 / ValidRemoval)
- **왜:** "의미 보존" 판단을 사람 기준으로 검증(리뷰 W1). 자동 판단만으론 부족.
- **어떻게:** `handoff/samples/04_human_factuality.csv` 형식대로 benign/altering 쌍에
  `human_equivalent`(0/1)를 사람 2명이 채움. Claude가 κ(일치도)와 ValidRemoval을 계산.

### B4. 공식 baseline 비교 (리뷰 W4) — ⭐ 실행 패키지 준비 완료
- **왜:** SynthID/SemStamp 등과 동일 조건 비교가 있어야 우열 주장 가능. 주 트랙 최대 관문.
- **준비됨(Claude):** 노트북 `handoff/Truthprint_W4_Baselines_Kaggle.ipynb`,
  스키마 `handoff/W4_SCHEMA_KO.md`, 절차 `handoff/KAGGLE_W4_STEPS_KO.md`,
  결정론적 채점기 `code/scripts/eval_baselines_real.py`(+테스트).
- **저자 작업(GPU):** 노트북 Settings(Internet On, GPU T4) → **Run All** →
  `w4_results.zip` 전달. 자체 완결형 KGW(실제 LLM+z-score)가 보장 baseline이라
  MarkLLM 없이도 실제 토큰-레벨 수치가 나옵니다. SynthID/SIR은 MarkLLM 선택 블록.
- **Claude가 받으면:** `eval_baselines_real.py`로 재채점(CI 확정) 후 §Experimental
  Methodology에 실데이터 head-to-head 비교표를 추가(진단 시뮬레이션은 이미 부록).

### B5. (선택) 실제 LLM 생성물로 확대
- 현재 원문은 템플릿 사실. 실제 LLM 생성 문장으로 `01`을 교체하면 외적 타당성↑.
  단, 그러면 폐쇄도메인 파서 밖이라 wide-coverage parser(아래 C 항목)가 선행돼야 함.

---

## C. Claude가 이어서 할 수 있는 것 (요청 시, 사람 데이터 없이도 일부 가능)
- **경량 neural/광역 파서**로 `multilingual.py` 확장(현재는 lexicon 규칙). 단, 이 환경엔
  GPU·모델 다운로드 제약이 있어, 저자 환경(Colab/Kaggle GPU)에서 돌릴 학습·평가 노트북을
  Claude가 작성해 드리는 형태가 현실적입니다.
- **W6 원고 재구성 — ✅ 완료:** 진단 시뮬레이션 표(Appendix A), Reproducibility·Notation
  (Appendix B), Software Architecture(C), Prototype Roadmap(D), Extended Evaluation
  Protocol=baselines/languages/attacks/metrics(E)를 부록으로 이동. 본문은 16개 섹션
  (Intro–Conclusion)으로 축소하고 RQ+평가 매트릭스는 본문 유지, 부록 포인터 한 줄 추가.
  상호참조·환경 균형·동기화 가드 모두 통과. 이 환경엔 `pdflatex`가 없으므로 **저자가
  로컬에서 `make acl`로 실제 8쪽 이내 여부만 최종 확인** 권장(초과 시 Related Work 압축이
  다음 후보).

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
- **Claude 자율 완료:** 코어 검증 + 오프라인 ablation + real-MT 음의 결과 + **6개 언어
  Stage-2/provenance 양의 실측**(어휘 완성·버그 수정 포함) + 원고 정직 반영(모두 `main`).
- **저자 최소 작업:** (B1) 노트북 Run All로 문서 수 늘려 CI 강화 — 지금 남은 **유일한 필수**
  작업. 나머지 B3–B5는 여력에 따라.
- **윤리:** D의 7개 항목은 저자 서명·판단 필요.
