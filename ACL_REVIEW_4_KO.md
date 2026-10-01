# Truthprint ACL 2027 모의 리뷰 4 — 심사 패널 시뮬레이션 (accept/publish 관점)

> 이 문서는 ACL 2027 심사 패널(리뷰어 3 + Area Chair)을 시뮬레이션한 네 번째 모의
> 리뷰다. 앞선 세 리뷰([`ACL_REVIEW_KO.md`](ACL_REVIEW_KO.md),
> [`ACL_REVIEW_2_KO.md`](ACL_REVIEW_2_KO.md), [`ACL_REVIEW_3_KO.md`](ACL_REVIEW_3_KO.md))
> 이후에 반영된 변경 — paraphrase/adaptive 평가(RQ4/RQ7), 확장 어휘집 방어, ledger
> retrieval(+NLI) baseline, 실제 LLM open-vocabulary neural 방어, 초록 압축·포지셔닝
> 정직화 — 를 반영한 **현재 `paper/acl_main.tex`(=`paper/main.tex` 동기화본)** 기준이다.
> 목적은 "제출"이 아니라 **accept/publish** 이므로, 각 리뷰어 점수와 함께 **합격을 가르는
> 레버**를 우선순위로 적는다. 최종 마감·페이지 제한·Responsible NLP 체크리스트는 제출
> 시점 공식 CFP에서 재확인해야 한다.

---

## 직전 리뷰(ACL_REVIEW_3) 이후 무엇이 달라졌나

- **paraphrase ≠ translation 축을 실측으로 채움.** benign 의미보존 paraphrase 인증
  TPR 1.000(RQ4), 스키마 인지 adaptive 공격 ValidRemoval(Eq. validremoval)을 오라클
  기준으로 보고(RQ7). (`paper/results/paraphrase.md`)
- **"그냥 저장·검색하면?"(W1)에 정량 답변.** 동일 ledger 가정·id-addressed 검증에서
  retrieval 0.047 / retrieval+NLI(proxy) 0.061 vs typed meaning-digest 1.000 tamper
  거부; oracle NLI만 1.000이나 필드 국소화·keyed tag 없음. (`paper/results/retrieval.md`)
- **적응 공격 방어를 3단계로 완결.** closed 어휘집(뚫림) → 확장 어휘집(seen 방어, held-out
  뚫림) → **실제 open-vocabulary neural(Llama-3.3-70B)이 held-out까지 방어**
  (held-out novel ValidRemoval 1.000→0.100, CI 분리; benign·tamper 1.000).
  (`paper/results/neural_defense.md`)
- **포지셔닝 정직화.** 초록(~470→~230단어)·결론·키워드를 "ledger 기반 authenticated
  semantic provenance(in-text 워터마크 아님)"로 재프레이밍하고 contract-collision FP
  floor를 명시.

→ 직전 패널의 최대 감점("closed-lexicon toy, 핵심이 미실증 neural에 의존")이 **상당 부분
완화**됨.

---

## Reviewer 1 — 경험주의 NLP (실세계 유효성 중시)

neural ①이 실제 LLM 추출로 메커니즘을 보인 것은 분명한 진전. 다만 그 실측은 **N=10·단일
모델·단일(폐쇄) 도메인** 으로 "proof-of-mechanism"이지 "result"는 아니다. 살아남는
meaning-digest는 여전히 템플릿 사실 위에서만, paraphrase는 규칙 기반(실제 paraphraser
아님).

- **Soundness 3.5 / Excitement 3.0 / Reproducibility 4.5 / Overall 3.0 (Findings 상단 /
  main 경계 하단) / Confidence 4**
- 합격 조건: neural 방어의 **규모화(N↑·복수 모델·개방 도메인)** 와 실제 LLM 생성물/
  paraphraser로의 확장.

## Reviewer 2 — 워터마킹·보안 (위협모델·포지셔닝 중시)

retrieval baseline + neural 방어로 포지셔닝 논거가 탄탄해졌고, 초록의 정직한 재프레이밍이
과설 우려를 줄였다. typed contract가 similarity/retrieval 대비 **tamper 국소화 + keyed
tag** 를 주고 open-vocab 커버리지는 LLM이 공급한다는 분업이 설득력 있다. 남은 감점: 실질
FP floor가 contract-collision(폐쇄도메인 5.2×10⁻³)이라 2⁻ᵗᵃᵘ 보증은 저엔트로피 텍스트에서
장식 — 개방/짧은 텍스트의 contract 엔트로피 실측이 필요.

- **Soundness 3.5 / Excitement 3.5 / Reproducibility 4.5 / Overall 3.5 (lean accept) /
  Confidence 4**

## Reviewer 3 — 이론·방법론 (엄밀성·정직성 평가)

claim–evidence 규율·조건부 정리·honest negative·CI에 더해, 이제
"공격 → 고정어휘집 방어 → held-out로 그 한계 노출 → open-vocab neural로 해소" 라는 서사가
완결적이다. 개념 기여(typed mutability contract)와 사중 실증(C1–C3 / matched-FPR /
retrieval / neural)이 강하다. 죽는 realization-carrier의 이론 지분이 아직 다소 큰 점,
규모가 작은 점이 아쉽다.

- **Soundness 4.0 / Excitement 3.5 / Reproducibility 4.5 / Overall 3.5 (accept-leaning) /
  Confidence 3**

## Area Chair — 메타리뷰 & 결정

세 리뷰가 수렴: 정직성·재현성·개념 novelty는 합격선이고, neural ① 실측이 "toy 한계"를
"메커니즘 입증, 규모만 남음"으로 바꿨다. 다만 main-track의 impact 바를 확실히 넘기려면
그 실측을 **규모화해 "결과화"** 하고 실데이터 축을 하나 더 채워야 한다.

- **결정: Findings of ACL 강한 accept / main-track 진짜 borderline(상향 가능).**
  (직전 "Findings 유력 / main reject-leaning"에서 상승.)

---

## Path to Accept — 갱신 우선순위 (잔여 레버)

| # | 조치 | 임팩트 | 비용 | 이 환경에서 실행 가능? |
|---|---|---|---|---|
| ①′ | neural 방어 **규모화**: N=10→수백, 복수 모델(번역기≠추출기), 개방 도메인 | ★★★ | ★★ | ✗ (OpenRouter 레이트리밋으로 스톨; 안정 GPU/API 필요) |
| ② | **실제 LLM/DIPPER paraphraser**로 RQ4/RQ7 (규칙기반 대체) | ★★ | ★★ | △ (생성은 API 필요 + 의미보존 판정에 사람/오라클 필요 → ⑤와 결합) |
| ③ | **real-MT provenance 스케일·CI 축소**(문서·언어↑) | ★★ | ★ | ✗ (NLLB 산출물이 repo에 없음; 저자 GPU/Kaggle 선행) |
| ④ | **초록 압축 + 포지셔닝 정직화** | ★★ | ★ | ✓ **완료**(본 리뷰 시점 반영) |
| ⑤ | **사람 factual-equivalence 주석**(RQ1/ValidRemoval gold 보강) | ★ | ★★ | ✗ (사람 주석자 필요) |
| ⑥ | **Arabic 약점** 완화/공정성 분석 | ★ | ★★ | △ (어휘집 코드 개선은 가능하나, 개선량 재측정에 NLLB 산출물 필요) |

**결론:** 현재 상태로 **Findings는 확정에 가깝고 main-track은 상향 가능한 borderline**이다.
main accept를 확실히 하려면 **①′(neural 규모화로 결과화)** 가 가장 효과적이며, ②·③가 뒤를
받친다. 이들 대부분은 **안정 GPU/API·NLLB 산출물·사람 주석** 이 선행돼야 하므로, 저자 측
자원 확보 후 실행하는 것이 경로다. ④는 이미 반영됐다.

---

## 재현 (이 리뷰가 근거로 삼은 수치)

```bash
cd code && pip install -e ".[dev]" && pytest -q          # 94 tests
truthprint selftest                                       # P1–P4, L1–L3
python3 scripts/eval_paraphrase.py                        # RQ4/RQ7 + 확장어휘집 방어
python3 scripts/eval_retrieval.py                         # ledger retrieval(+NLI) baseline
python3 scripts/eval_neural_defense.py --use-cache        # open-vocab neural 방어 (키 불필요)
```

결과 파일: `paper/results/{paraphrase,retrieval,neural_defense}.md`(+`.json`),
`neural_defense_cache.jsonl`(키 없이 재현용 캐시).
