# Truthprint ACL 제출 전 모의 리뷰

## 한줄 판정

**현재 원고 그대로라면: Reject (대략 2/5, 확신도 4/5).** 아이디어의 문제 설정과
구조화된 불변량 계약은 흥미롭지만, ACL의 실증 논문으로 판단할 때 핵심 주장이 아직
실제 다국어 생성·번역·패러프레이즈 실험으로 검증되지 않았다. 현재 결과는 코딩 계층의
시뮬레이션과 폐쇄 도메인 템플릿 실험이므로, 논문 스스로 제시하는 “translation- and
paraphrase-robust” 주장을 뒷받침하기에는 부족하다.

> 이 평가는 저장소의 현재 `paper/main.tex`, 구현, 재현 스크립트를 대상으로 한 내부
> 모의 리뷰다. 특정 연도의 공식 ARR/ACL 마감, 페이지 제한, 체크리스트는 제출 시점의
> 공식 CFP에서 다시 확인해야 한다.

## 예상 점수표

| 항목 | 예상 점수 | 평가 |
|---|---:|---|
| 독창성 / 신규성 | 3/5 | typed invariant contract와 authenticated payload의 결합은 명확한 차별점이지만, semantic/AMR watermarking 대비 새 학습·추론 알고리즘은 아직 약함 |
| 기술적 타당성 | 2/5 | 암호·소거 코딩 코어는 타당하나, “semantic fidelity by construction”은 완전한 parser/validator를 가정해 실제 NLP 오류를 우회함 |
| 실증적 건전성 | 1–2/5 | 실제 MT/LLM/semantic parser가 없는 합성 채널 결과가 핵심 약점 |
| 중요성 | 3–4/5 | 번역·패러프레이즈 후 provenance는 중요하고 시의성 있는 문제 |
| 흥미성 | 3/5 | negation/quantity/attribution을 명시적으로 잠그는 관점은 NLP 독자에게 흥미로움 |
| 명료성 | 3/5 | 문제와 파이프라인은 명료하나 범위가 넓고 roadmap/계획이 결과처럼 혼재 |
| 재현성 | 4/5 (Stage-1 한정) | 코드와 고정 seed가 있고 테스트가 통과하지만, 재현되는 것이 최종 시스템 성능은 아님 |
| 종합 | 2/5 | 아이디어는 유망하나 ACL accept에 필요한 end-to-end evidence가 없음 |

## 강점

1. **문제가 중요하고 명확하다.** 토큰 수준 워터마크가 표면형 변환에 취약하다는 문제를
   “불변 의미”와 “허용된 실현 선택”의 분리로 재정의한 것은 좋은 framing이다.
2. **차별점을 논문이 스스로 비교적 정확히 말한다.** 임베딩 거리 대신 필드별 typed
   predicate로 허용 가능성을 정의하고, invariant digest에 MAC을 결합한다는 점은 단순히
   “더 좋은 semantic similarity”를 주장하는 것보다 선명하다.
3. **보수적인 실패 처리가 좋다.** 불확실한 carrier를 잘못된 bit로 읽지 않고 erasure로
   취급하며, 용량이 부족하면 abstain하도록 설계한 점은 실제 provenance 시스템의
   요구와 잘 맞는다.
4. **주장 일부는 재현 가능하다.** canonical digest, HMAC, keyed mapping, GF(2) erasure
   decoding이 구현되어 있고 단위 테스트가 있다.
5. **한계를 숨기지 않는다.** 폐쇄 도메인 Stage-1임을 명시하고 wide-coverage semantic
   parsing을 미해결 문제로 인정한다.

## 치명적 약점(accept를 막는 요소)

### 1. 핵심 결과가 실제 번역 결과가 아니라 매개변수화된 합성 채널이다

번역 표의 EN→KO/HI 수치는 실제 번역기 출력에서 측정한 carrier 생존율이 아니다.
`tau_tok`과 `epsilon_inv`를 미리 정하고 각 방법의 생존 확률을 방법별 공식으로
**유도**한다. 따라서 “token methods collapse, semantic methods survive”라는 결론은
실험으로 발견한 결과라기보다 simulator에 넣은 가정의 결과다. 특히 SWAN 1.000,
Truthprint 0.972–1.000과 같은 숫자는 실제 parser 오류, 자연스러움, 생성 실패, 문장
정렬 실패를 반영하지 않는다. 리뷰어는 이를 circular evaluation 또는 toy simulation으로
볼 가능성이 높다.

**필수 수정:** 최소 3개 언어쌍에서 실제 MT 시스템 2종 이상을 사용하고, 원문 생성부터
번역, 재파싱, 검출까지 end-to-end로 실행한다. 각 언어쌍마다 실제 carrier survival,
payload recovery, TPR@고정 FPR, abstention, semantic error를 함께 보고한다.

### 2. 제안 시스템의 핵심인 semantic frontend가 존재하지 않는다

현재 linguistic layer는 두 carrier(능동/수동, 시간구 위치)와 템플릿 사실 문장을
다루는 규칙 기반 closed-domain demo다. 하지만 논문의 큰 주장은 개체, 의미역, 양화,
시제, modality, causality, attribution 등 넓은 불변량과 다국어 정규화에 의존한다.
실제 parser가 틀리면 다음 두 경우가 모두 생긴다.

- 의미가 바뀌었는데 같은 invariant로 읽어 false attribution이 발생한다.
- 의미가 보존됐는데 다른 invariant로 읽어 MAC이 실패한다.

현재 정리의 `InvariantEq`와 validator가 완전하다는 가정은 이 문제를 해결하지 않고
성공 조건으로 옮겨 놓는다. 따라서 “semantic fidelity by construction”은 **IR 내부의
조건부 명제**로는 맞지만 실제 자연어 시스템의 보장은 아니다.

**필수 수정:** 실제 multilingual parser/SRL/AMR/LLM structured extraction을 구현하고,
불변량 필드별 precision/recall 및 변환 전후 consistency를 수작업 주석 gold set에서
측정한다. 정리의 명칭과 초록도 “assuming sound invariant validation”이라는 조건을
명시해야 한다.

### 3. baseline 비교가 공정한 end-to-end 비교가 아니다

baseline은 원 논문의 실제 생성기·검출기가 아니라 “detection statistic과 signal
placement의 faithful reduction”이다. 동시에 Truthprint만 실제 템플릿 문장과 BLEU-1을
사용하고 baseline 품질은 측정하지 않는다. 서로 다른 추상화를 같은 표에 놓은 결과는
우열의 근거가 되기 어렵다. SynthID-Text와 KGW도 서로 다른 방법인데 한 행으로 묶여
있어 attribution이 불명확하다.

**필수 수정:** 공개 공식 구현 또는 널리 쓰이는 toolkit으로 각 baseline을 동일한 LLM,
prompt, 길이, decoding budget에서 실행한다. SynthID와 KGW는 분리한다. SemStamp,
SemaMark/SIR, SWAN 등 가장 가까운 semantic baseline과 실제 공격 출력에서 비교하고,
모든 방법에 동일한 quality 및 latency 지표를 적용한다.

### 4. 신규성의 중심이 아직 “설계 문서”에 가깝다

typed mutability, MAC, ECC, erasure 처리는 각각 합리적이지만 개별 요소는 알려진
구성요소다. accept를 위해서는 결합 자체가 새로운 시스템 성질을 만든다는 증거가
필요하다. 현재는 SWAN 대비 “각 필드를 mutability로 typing”한다는 설명이 있으나,
어떤 현상에서 SWAN/embedding 방법이 실패하고 Truthprint가 성공하는지 실제 최소
대조쌍 결과가 없다.

**필수 수정:** negation, number, temporal scope, modality, attribution, causal direction별
challenge set을 만들고 다음 ablation을 수행한다.

- full Truthprint
- invariant validation 제거
- MAC binding 제거
- ECC/erasure 제거
- embedding-only admissibility
- structure-only 또는 AMR baseline

이 결과로 각 구성요소가 fidelity, robustness, forgery resistance에 기여함을 보여야 한다.

### 5. ACL 형식은 마련됐지만 제출 준비는 아직 끝나지 않았다

저장소에는 이제 `acl` review option을 사용하고 저자 정보를 제거한
`paper/acl_main.tex`이 있으며, canonical 원고로부터 재생성·동기화 검사도 가능하다.
다만 현재 분량과 폭넓은 background, roadmap, software architecture는 ACL 본문 예산에서
핵심 실험을 밀어낼 가능성이 크다. 실제 제출 연도의 페이지 제한,
limitations/ethics/responsible NLP checklist, artifact 정보도 최종 확인해야 한다.

**필수 수정:** 익명 ACL source의 형식 검사는 유지하되 background를 축약한다.
“Prototype Roadmap”, 미래형 “Experimental Methodology”, 상세 software skeleton은
appendix로 이동하고, 확보한 공간을 실제 experiments와 error analysis에 사용한다.

## 주장별 위험도

| 현재 주장 | 위험 | 권장 표현/증거 |
|---|---|---|
| “language-independent IR” | 높음 | 최소 3개 typologically diverse language에서 동일 predicate/role inventory의 정량 검증 |
| “translation-robust” | 매우 높음 | 실제 MT 및 round-trip/two-hop 출력의 end-to-end 검출 결과가 생기기 전에는 “designed for”로 제한 |
| “paraphrase-robust” | 매우 높음 | 여러 LLM/공격 강도, detector-guided adaptive attack 결과 필요 |
| “semantic fidelity by construction” | 높음 | parser/validator soundness 조건을 정리에 포함하고 human factuality 결과 병기 |
| “FPR bounded by 2^-tau” | 중간 | MAC verification conditional FPR과 전체 pipeline의 statistical FPR을 명확히 분리 |
| “unforgeability” | 중간 | nonce/key lifecycle, replay, splicing, chosen-message/detection-oracle 모델을 명시하고 공격 실험 추가 |
| EU AI Act compliance framing | 중간–높음 | 법적 준수 보장처럼 읽히지 않게 motivation으로 제한하고 법률 해석은 신중히 표현 |

## ACL accept 가능성을 높이는 최소 실험 패키지

### 데이터와 생성

- 3개 이상 도메인(뉴스/위키형 사실 설명/기술 문서), 도메인당 충분한 문서 수.
- EN, KO, HI를 최소 축으로 하고 가능하면 ZH/AR 추가.
- 동일한 1–2개 공개 LLM에서 원문을 생성하며 prompt와 decoding 조건을 고정.
- 문서 길이별 구간을 나눠 capacity/abstention curve를 보고.

### 변환/공격

- 실제 MT 2종, round-trip, pivot translation.
- LLM paraphrase 2종 × 강도 3단계.
- summarization compression ratio 25/50/75%.
- 문장 삭제/삽입/splicing 및 detector-guided adaptive rewrite.
- 공격 성공은 watermark 제거뿐 아니라 의미 보존을 통과해야 하며,
  `ValidRemoval = removal AND semantic preservation`으로 평가.

### 지표

- TPR at 1%, 0.1%, 0.01% FPR와 bootstrap 95% CI.
- authenticated full/partial payload recovery, BER, abstention rate.
- 필드별 invariant precision/recall/consistency와 human factual equivalence.
- fluency/preference human evaluation, LLM-as-judge는 보조 지표로만 사용.
- latency, candidate rejection rate, carriers/sentence, 최소 신뢰 길이.
- 공격 strength/semantic drift에 따른 Pareto curve.

### 통계 설계

- 문서 단위 split과 paired bootstrap 또는 permutation test.
- threshold calibration set과 final test set 완전 분리.
- seed 여러 개, 평균±CI 보고; 0/20,000은 “0”만 쓰지 말고 이항 신뢰상한 보고.
- baseline별 동일 false-positive operating point와 동일 텍스트 길이 보장.

## 권장 논문 재구성

1. **Introduction:** 문제, 한 문장의 핵심 아이디어, 3개 기여로 축약.
2. **Related Work:** token / semantic / structured / cryptographic의 네 묶음만 유지.
3. **Method:** IR contract, encoder, detector, 명시적 assumptions.
4. **Analysis:** conditional fidelity, authentication, capacity를 짧게 정리.
5. **Experimental Setup:** 실제 모델·데이터·언어·공격·baseline·통계.
6. **Results:** main robustness table, semantic fidelity, ablation, adaptive attacks.
7. **Error Analysis:** parser 실패, carrier 부족, 언어별 실패 유형.
8. **Limitations & Ethics:** 오탐 사용 위험, 접근 통제, privacy, false accusation.

## 더 날카로운 기여문 예시

기존의 7개 contribution bullet은 너무 많고 설계·계획·구현이 섞여 있었다. 원고에서는
이를 다음 세 범주(method, conditional analysis, Stage-1 evidence/protocol)로 줄였다.

1. **Method:** “We formulate semantic watermark carriers as key-dependent
   realization choices constrained by a typed, field-level invariant contract.”
2. **Guarantee:** “Conditioned on sound invariant extraction and validation,
   encoding preserves protected fields; invariant-bound authentication separates
   provenance verification from statistical detectability.”
3. **Evidence:** “Across real multilingual translation and paraphrase pipelines,
   we evaluate robustness, semantic fidelity, capacity, and adaptive removal against
   token-, embedding-, and AMR-based baselines.”

세 번째 문장은 해당 실험을 실제로 수행한 뒤에만 사용할 수 있다.

## 추천 의사결정

- **현재 마감에 즉시 제출:** 비추천. 형식 문제가 해결되어도 핵심 experimental
  validation 부재로 reject 가능성이 높다.
- **4–8주 내 제한된 개선:** workshop/demo/system demonstration 성격이라면 가능하나,
  main ACL 경쟁력은 여전히 낮다.
- **end-to-end multilingual frontend + 실제 baseline 실험 후 제출:** 추천. 이 경우
  novelty는 3/5 수준이어도 중요성, 실증성, 재현성의 조합으로 borderline accept 이상을
  노릴 수 있다.

## 최종 우선순위

1. 실제 multilingual end-to-end system 구현.
2. 실제 공식 baseline과 공정 비교.
3. semantic-field challenge set 및 ablation.
4. adaptive attack, replay/splicing, parser 오류 분석.
5. 주장 축소와 ACL 형식/익명화.

가장 중요한 메시지는 단순하다. **현재 원고의 장점은 좋은 아이디어와 명료한 시스템
계약이고, 가장 큰 결함은 그 계약이 실제 자연어 파이프라인에서도 성립한다는 증거가
없다는 점이다.** ACL accept를 위해서는 더 많은 설명보다 실제 end-to-end evidence가
우선이다.

## 이번 리뷰를 반영해 원고에 적용한 수정

- ACL review 형식의 익명 원고와 canonical source 동기화 검사를 마련했다.
- 초록과 본문 전반에서 translation/paraphrase robustness를 실증 결과가 아니라 향후
  검증할 설계 목표로 제한했다.
- contribution을 세 항목으로 압축해 제안 방법, 조건부 분석, 실제로 확보한 Stage-1
  증거를 분리했다.
- fallback 통계 검출기의 시스템 FPR까지 암호학적 tag bound가 보장하는 듯한 표현을
  제거하고, held-out calibration이 별도로 필요함을 명시했다.
- EU AI Act를 준수 보장이나 법률 해석으로 연결하지 않고 연구 동기로만 한정했다.
- 합성 baseline 표를 diagnostic simulation으로 명시하고 실제 모델·공식 baseline의
  성능 비교로 인용해서는 안 된다고 표시했다.

이 수정은 과장과 제출 형식 위험을 줄이지만, 위 1--4번의 핵심 실증 결손을 해결하지는
않는다. 따라서 현재 모의 판정은 그대로 Reject이며, 실제 다국어 end-to-end 실험 없이
표현 수정만으로 점수를 상향해서는 안 된다.
