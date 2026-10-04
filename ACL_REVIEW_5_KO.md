# Truthprint ACL 2027 모의 리뷰 5 — 심사 패널 시뮬레이션 (accept/publish 관점)

> ACL 2027 심사 패널(리뷰어 3 + Area Chair)을 시뮬레이션한 다섯 번째 모의 리뷰다.
> 앞선 네 리뷰([`ACL_REVIEW_KO.md`](ACL_REVIEW_KO.md),
> [`ACL_REVIEW_2_KO.md`](ACL_REVIEW_2_KO.md), [`ACL_REVIEW_3_KO.md`](ACL_REVIEW_3_KO.md),
> [`ACL_REVIEW_4_KO.md`](ACL_REVIEW_4_KO.md)) 이후 반영된 **가장 큰 변경** — 실제
> **4,800건 NLLB-200 번역 런(B2)을 저장소에 커밋**하고 §Stage-2/§Provenance의 모든
> 수치를 그 원시 데이터로부터 **GPU 없이 재현 가능**하게 교체한 것 — 을 반영한 현재
> `paper/acl_main.tex`(=`paper/main.tex` 동기화본) 기준이다. 목적은 "제출"이 아니라
> **accept/publish** 이므로, 각 리뷰어 점수와 함께 **합격을 가르는 레버**를 우선순위로 적는다.
> 최종 마감·페이지 제한·Responsible NLP 체크리스트는 제출 시점 공식 CFP에서 재확인해야 한다.

---

## 직전 리뷰(ACL_REVIEW_4) 이후 무엇이 달라졌나

- **실데이터 축이 "미실증 → 저장소 내 재현"으로 전환.** 직전 패널이 남긴 최대 잔여 레버
  ③(real-MT provenance 스케일·CI 축소, repo에 NLLB 산출물 부재)이 해소됐다. 50개 source
  문서 × 16문장 = 800개 항목, **6개 조건(ko/hi/zh/ar/de + round-trip) 4,800건 번역**의
  원시 데이터를 `paper/results/realmt_b2/`에 커밋했고, §Stage-2·§Provenance의 모든 숫자가
  커밋된 eval 스크립트로 **키·GPU 없이** 재현된다.
- **정직한 하향 보정.** 이전의 검증 불가한 off-repo 수치를, 재현 가능한 실제 런으로 교체하면서
  일부 수치가 **낮아졌다**. 닫힌 범주형(polarity/quantity/time/attribution)은 **≥0.97**로
  유지, 낮아진 쪽은 열린 entity/relational 필드(patient 0.825, predicate/modality/causation
  ≈0.86)다. core6 문서 귀속은 DE/HI **1.000**, 나머지 **0.90–0.98**(AR 최저 0.900), tamper
  거부 **≥0.996**, FP **0.000–0.007**.
- **fidelity/robustness 트레이드오프를 측정값으로 명시.** full9로 계약을 넓히면 의미 포괄은
  늘지만 TPR이 떨어지고(AR 0.253) 최난 조건의 문서 귀속이 붕괴(AR 0.02, ZH 0.08, RT 0.24)
  하는 반면 DE/HI는 0.94로 유지 — 선택 가능한 운영점으로 제시.
- **FP-floor 예측이 실측과 닫힘.** contract-collision floor(core6 ≈1/192 = 5.2×10⁻³) 예측이
  실측 FP 0.000–0.007 범위와 일치함을 같은 커밋 런에서 확인.

→ 직전 패널이 "저자 자원(GPU/Kaggle) 선행"으로 분류했던 핵심 레버가 **실행 완료**됐고,
재현성·실데이터 규모가 올라갔다. 동시에 숨어 있던 약점(AR·full9)이 **정직하게 노출**됐다.

---

## Reviewer 1 — 경험주의 NLP (실세계 유효성 중시)

real-MT 결과가 이제 "메커니즘 입증"을 넘어 **4,800건 규모의 재현 가능한 결과**가 됐다는 점이
가장 큰 진전이다. 숫자가 이전보다 낮아졌지만, off-repo 미검증 수치를 저장소 내 재현 수치로
바꾼 것이므로 신뢰도는 **올라간다**(나는 이런 하향 보정을 감점이 아니라 가점으로 본다). 닫힌
범주형이 ≥0.97로 번역을 견디는 것은 설득력 있다. 남는 한계: (i) 추출기가 **단일 모델·폐쇄
도메인 템플릿 사실** 위에서 측정됐고, (ii) **Arabic·full9 운영점은 실사용엔 약하다**(AR full9
문서귀속 0.02). paraphrase 축은 여전히 규칙 기반.

- **Soundness 4.0 / Excitement 3.0 / Reproducibility 5.0 / Overall 3.5 (main 경계) /
  Confidence 4**
- 합격 조건: neural 추출 방어의 **규모화**(복수 모델·개방 도메인·실 생성물)와 AR 등 약 조건의
  개선 또는 공정성 분석.

## Reviewer 2 — 워터마킹·보안 (위협모델·포지셔닝 중시)

예측한 contract-collision FP floor(≈1/192)가 **같은 커밋 런의 실측 FP(0.000–0.007)와 닫힌
것**이 좋다 — 이론·실측 정합이 보안 주장(2⁻ᵗᵃᵘ는 저엔트로피 계약에서 장식)을 구체화한다.
typed contract가 tamper 국소화 + keyed tag를 주고 open-vocab 커버리지는 LLM이 공급한다는
분업도 유지된다. full9/core6 트레이드오프를 **운영점으로 명시**한 것도 위협모델 관점에서
정직하다. 남은 감점: 개방/짧은 텍스트의 contract 엔트로피 실측(배치 FP floor)이 여전히
미실증 — 폐쇄도메인 4,800건은 여전히 상한 추정.

- **Soundness 3.5 / Excitement 3.5 / Reproducibility 5.0 / Overall 3.5 (lean accept) /
  Confidence 4**

## Reviewer 3 — 이론·방법론 (엄밀성·정직성 평가)

claim–evidence 규율·조건부 정리·honest negative에 더해, 이번에 **원시 데이터를 커밋하고
수치를 하향 보정한 것**은 이 분야에서 드문 수준의 정직성이다. 모든 §Stage-2/§Provenance 숫자가
GPU 없이 재현되고, FP-floor 예측↔실측이 같은 런에서 닫히며, fidelity/robustness 트레이드오프가
측정 곡선으로 제시된다. 개념 기여(typed mutability contract)와 다중 실증(C1–C3 / matched-FPR
/ retrieval / neural / real-MT)이 강하다. 아쉬운 점: 죽는 realization-carrier의 이론 지분,
문서 수(50)·추출기 다양성이 아직 작다.

- **Soundness 4.0 / Excitement 3.5 / Reproducibility 5.0 / Overall 4.0 (accept) /
  Confidence 4**

## Area Chair — 메타리뷰 & 결정

세 리뷰가 수렴한다: 정직성·재현성·개념 novelty는 확실히 합격선이고, 이번 B2 커밋으로
**실데이터 축이 "저자 자원 대기"에서 "저장소 내 완전 재현"으로 넘어갔다**. 숫자의 정직한 하향과
원시 데이터 공개는 신뢰도를 높이는 방향이며, 트레이드오프·FP-floor 정합이 보안 주장을 구체화한다.
main-track impact 바를 확실히 넘기려면 남은 레버는 **neural 추출 방어의 규모화(①′)**와
**추출기·도메인 다양성**이다 — 둘 다 결과를 바꾸기보다 일반화를 넓히는 작업이다.

- **결정: Findings of ACL 확정적 accept / main-track borderline → lean accept(상향).**
  (직전 "Findings 강한 accept / main 진짜 borderline"에서 상승.)

---

## Path to Accept — 갱신 우선순위 (잔여 레버)

| # | 조치 | 임팩트 | 비용 | 이 환경에서 실행 가능? |
|---|---|---|---|---|
| ①′ | neural 추출 방어 **규모화**: N↑, 복수 모델(번역기≠추출기), 개방 도메인 | ★★★ | ★★ | ✗ (안정 GPU/API 선행; OpenRouter 레이트리밋으로 스톨) |
| ② | **실제 LLM/DIPPER paraphraser**로 RQ4/RQ7 (규칙기반 대체) | ★★ | ★★ | △ (생성은 API, 의미보존 판정에 사람/오라클 → ⑤와 결합) |
| ③ | **real-MT provenance 스케일·CI·in-repo 재현** | ★★ | ★ | ✓ **완료**(본 리뷰 시점 반영, `realmt_b2/` 커밋) |
| ④ | **초록 압축 + 포지셔닝 정직화** | ★★ | ★ | ✓ **완료**(리뷰 4에서 반영) |
| ⑤ | **사람 factual-equivalence 주석**(RQ1/ValidRemoval gold 보강) | ★ | ★★ | ✗ (사람 주석자 필요) |
| ⑥ | **Arabic·full9 약점** 완화/공정성 분석 | ★★ | ★★ | △ (추출기 코드 개선은 가능; 개선량 재측정에 번역 산출물 재생성 필요) |
| ⑦ | **문서 수↑·추출기 다양성**(일반화 폭) | ★★ | ★★ | △ (추가 번역 런 필요) |

**결론:** 이번 B2 통합으로 **Findings는 사실상 확정**이고 **main-track은 borderline에서 lean
accept로 상향**됐다. main accept를 굳히려면 남은 가장 효과적인 레버는 **①′(neural 규모화)**이며
⑥·⑦(AR·full9 약점 완화, 일반화 폭)이 뒤를 받친다. 이들은 대부분 **안정 GPU/API·추가 번역 런·
사람 주석** 이 선행돼야 하므로 저자 측 자원 확보 후 실행하는 것이 경로다. ③·④는 이미 반영됐다.

---

## 재현 (이 리뷰가 근거로 삼은 수치)

```bash
cd code && pip install -e ".[dev]" && pytest -q          # 97 tests
python3 -m truthprint.cli selftest                        # P1–P4, L1–L3
python3 scripts/eval_multilingual.py                      # §Stage-2: realmt_b2/에서 재현
python3 scripts/eval_provenance.py                        # §Provenance: realmt_b2/에서 재현
python3 scripts/eval_paraphrase.py                        # RQ4/RQ7 + 확장어휘집 방어
python3 scripts/eval_retrieval.py                         # ledger retrieval(+NLI) baseline
python3 scripts/eval_neural_defense.py --use-cache        # open-vocab neural 방어 (키 불필요)
python3 scripts/eval_semantic_fp.py                       # contract-collision FP floor + crossover
```

원시 데이터(커밋됨): `paper/results/realmt_b2/{01_source_items,02_transformations}.jsonl`
(800 항목 / 4,800 번역). 재생성 결과: `paper/results/{stage2_multilingual,provenance_realmt}.{md,json}`.
기타 결과 파일: `paper/results/{paraphrase,retrieval,neural_defense,semantic_fp}.md`(+`.json`),
`neural_defense_cache.jsonl`(키 없이 재현용 캐시).
