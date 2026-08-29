# Truthprint ACL 모의 리뷰 2: 이론·보안 및 실증 관점

## 총평

**판정: Reject (2/5), 확신도 5/5.** 첫 번째 리뷰보다 이 리뷰는 아이디어의 매력보다
주장과 증거 사이의 논리적 연결을 엄격하게 본다. typed invariant contract는 유용한
설계 원칙이고 MAC/ECC 결합도 합리적이지만, 현재 논문은 완성된 NLP watermarking
시스템의 평가라기보다 시스템 명세와 코딩 코어의 proof of concept에 가깝다. ACL main
conference에서 요구할 핵심 증거인 실제 생성 품질, 다국어 parser 정확도, 변환 후 검출,
공정한 baseline 비교가 없다.

## 점수와 근거

| 평가축 | 점수 | 근거 |
|---|---:|---|
| 기여도 | 3/5 | 의미 보존을 field-level contract로 다룬 framing은 유용하지만 NLP frontend가 구현되지 않음 |
| 기술적 건전성 | 2/5 | 조건부 정리 자체는 합리적이나 핵심 조건인 validator soundness가 검증되지 않음 |
| novelty | 2.5/5 | 기존 semantic/structured watermark에 mutability typing, MAC, ECC를 결합한 system novelty; 새 학습법이나 decoding algorithm은 아님 |
| 실험 | 1/5 | synthetic erasure와 closed template만으로 실제 MT/LLM robustness를 판단할 수 없음 |
| 명료성 | 4/5 | 한계 표시는 좋아졌으나 본문에 roadmap과 미래 실험이 과도함 |
| 재현성 | 4/5 (코어만) | 코딩·암호 계층은 재현 가능하지만 논문의 중심 NLP 주장은 재현 대상이 아님 |

## 강점

1. **실패를 erasure로 처리한다.** 불확실한 carrier를 억지로 bit로 읽지 않는 보수적
   설계는 실제 provenance 시스템에 적합하다.
2. **인증과 통계 검출을 분리할 가능성이 있다.** payload recovery 뒤 MAC을 확인하는
   구조는 단순 similarity score보다 provenance claim을 명확하게 만들 수 있다.
3. **의미 오류 유형이 구체적이다.** negation, number, temporal scope, modality,
   attribution, causal direction을 별도 필드로 보는 것은 generic embedding similarity의
   맹점을 잘 드러낸다.
4. **재현 가능한 코어가 있다.** canonicalization, keyed mapping, GF(2) erasure decoding,
   truncated HMAC의 조합은 실행 가능한 artifact로 제공된다.

## 주요 지적사항

### 1. 정리의 가장 강한 가정이 실제 연구 문제와 동일하다

protected-field fidelity는 sound parser/validator를 가정한다. 그러나 번역과
패러프레이즈 뒤 negation, scope, attribution을 동일하게 복원하는 sound frontend가 바로
해결해야 할 NLP 문제다. 이 가정 아래의 명제는 IR 내부 일관성을 보여주지만 자연어
출력의 사실 보존을 증명하지 않는다.

**요구 실험:** field별 extraction precision/recall, 변환 전후 consistency, human
factual-equivalence를 보고하고 parser confidence에 따른 fidelity--coverage curve를
제시하라. 전체 문장을 하나의 accuracy로 합치지 말고 polarity, number, time,
attribution, causality를 분리하라.

### 2. nonce를 detector가 어떻게 얻는지 정의되지 않았다

reference API는 nonce를 detector 입력으로 받는다. 실제 텍스트에서 nonce를 먼저 알아야
keyed carrier mapping을 역산할 수 있으므로, out-of-band lookup인지 후보 nonce 탐색인지
프로토콜이 필요하다. 후보 key--nonce 수가 늘면 tag verification 기회와 시스템 FPR도
늘어난다.

**요구 수정:** nonce discovery, key rotation, registry retention, collision/reuse 정책을
명시하고 후보 수에 따른 latency와 false-positive budget을 평가하라.

### 3. 보안 게임에서 forgery, replay, splicing이 혼재한다

유효한 기존 문서의 재전송은 MAC forgery가 아니다. 인증된 문단을 다른 문서에 삽입하는
splicing도 document-level provenance와 paragraph-level provenance에서 의미가 다르다.
기존 theorem의 fresh tuple 조건은 forgery만 다루므로, 배포 주장을 그보다 넓게 읽으면
안 된다.

**요구 수정:** (a) fresh-payload forgery, (b) exact replay, (c) paragraph splicing,
(d) detector-oracle removal을 별도 게임과 지표로 정의하라. paragraph ID와 document root
binding을 포함한 대안을 ablation하라.

### 4. tag bound는 end-to-end FPR이 아니다

$2^{-\tau}$는 독립적인 한 candidate가 idealized tag check를 통과할 확률이다. parser가
여러 후보 payload, nonce, key를 탐색하면 union bound의 시험 횟수가 필요하다. statistical
fallback은 전혀 다른 calibration 문제다. MAC의 EUF-CMA advantage에 blind-guessing 항을
다시 더하면 동일 위험을 이중 계산할 수도 있다.

**적용한 수정:** 원고는 fresh-payload EUF-CMA reduction과 ideal-PRF candidate bound를
분리하고, guessing loss가 EUF-CMA advantage에 이미 포함됨을 명시하도록 수정했다.

### 5. novelty는 구성요소가 아니라 상호작용으로 입증해야 한다

typed schema, MAC, ECC, semantic carrier는 각각 알려진 아이디어다. 따라서 novelty는
결합이 만드는 새로운 Pareto improvement로 보여야 한다. 현재는 그 상호작용을 실제
텍스트에서 검증하지 않았다.

**필수 ablation:** full model, no validator, embedding-only validator, no invariant
binding, no ECC, no erasure abstention, structure-only baseline을 같은 generation budget과
고정 FPR에서 비교하라.

### 6. diagnostic baseline 표는 삭제 또는 appendix 이동이 낫다

token replacement parameter를 크게 설정하고 token proxy가 붕괴하는 결과는 channel
정의의 직접적 귀결이다. 명확한 disclaimer가 있어도 독자는 숫자를 실제 baseline
성능으로 오해할 수 있다. 특히 Truthprint만 실제 문장 BLEU를 보고하고 다른 방법은
quality를 측정하지 않아 main result table로는 공정하지 않다.

**권고:** 본문에서는 simulator regression test만 한 문장으로 언급하고 수치 표는
appendix/artifact로 이동하라. 확보한 공간에 claim--evidence table과 실제 error case를
배치하라.

## ACL 제출을 위한 최소 조건

1. 실제 LLM 2종, MT 2종, 최소 3개 언어쌍의 end-to-end 결과.
2. 공식 또는 저자가 검증한 baseline 구현과 동일 generation/quality budget.
3. 문서 단위 held-out calibration 및 TPR@0.1%/0.01% FPR의 bootstrap confidence interval.
4. semantic-field challenge set과 사람 주석 기반 frontend 평가.
5. replay, splicing, adaptive removal 및 nonce-search 실험.
6. full component ablation과 capacity/abstention/length curve.

## 반영된 원고 변경

- demonstrated, conditional, not established를 구분하는 claim--evidence table을 추가했다.
- EUF-CMA theorem에서 blind guessing을 중복 가산하지 않도록 fresh-forgery 표현을 고쳤다.
- per-candidate tag bound와 end-to-end FPR/calibration을 분리했다.
- nonce가 reference API에 out-of-band로 주어짐을 공개하고 nonce resolution, replay,
  splicing의 배포 요구사항을 추가했다.

이 변경은 논리적 범위를 더 정확히 만들지만 새로운 실험 증거를 만들지는 않는다.
따라서 현재 판정은 유지한다.
