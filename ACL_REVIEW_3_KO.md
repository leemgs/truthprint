# Truthprint ACL 2027 모의 리뷰 3 — ARR 리뷰 폼 관점의 최종 심사

> 이 문서는 ACL 2027 / ARR 리뷰어 관점에서 저장소의 현재 `paper/acl_main.tex`(=`paper/main.tex`
> 본문 동기화본), 참조 구현(`paper/reference/`, `code/`), 재현 스크립트를 대상으로 작성한
> 세 번째 모의 리뷰다. 앞선 두 리뷰([`ACL_REVIEW_KO.md`](ACL_REVIEW_KO.md),
> [`ACL_REVIEW_2_KO.md`](ACL_REVIEW_2_KO.md))가 각각 "실증 준비성"과 "이론·보안 범위"에
> 집중했다면, 이 리뷰는 **ARR 공식 리뷰 폼의 축(Soundness / Excitement / Reproducibility /
> Overall)** 에 따라 재판정하고, 특히 **"이 논문의 진짜 정체성이 무엇이며, 그 정체성으로
> 판단할 때 어느 트랙에서 accept 가능한가"** 를 명확히 한다. 최종 마감·페이지 제한·
> Responsible NLP 체크리스트는 제출 시점 공식 CFP에서 재확인해야 한다.

---

## 0. 한 줄 판정 (메타리뷰 요약)

**현재 원고를 ACL 2027 main track 장편(long paper)으로 제출하면: Weak Reject
(Overall 2.5/5, Confidence 4/5).** 다만 이는 "나쁜 논문"이라는 뜻이 아니라 **"트랙이
어긋났다"** 는 뜻에 가깝다.

- 이 논문의 실제 기여는 *새로운 실증 SOTA 시스템*이 아니라 **(a) watermark 전용
  typed invariant 계약이라는 설계 프레임과 (b) 그 계약의 암호·소거코딩 코어에 대한
  재현 가능한 검증, (c) 반증 가능한(falsifiable) 평가 프로토콜의 사전 등록**이다.
- 이 정체성으로 보면 논문은 **honest하고 잘 짜인 design + verified-core + protocol
  논문**이며, 그 자체로 완성도가 낮지 않다. 문제는 초록·제목·표가 여전히 독자에게
  "번역·패러프레이즈 강건성 시스템"을 기대하게 만든다는 점, 그리고 main track 리뷰어는
  그 기대에 대한 end-to-end 증거를 요구한다는 점이다.
- **경로 판단:**
  - *실제 다국어 end-to-end 실험을 붙이면* → main track borderline accept 권으로 진입 가능.
  - *실험 없이 지금 형태로 간다면* → **Findings of ACL** 또는 **TrustNLP / 워터마킹 계열
    워크숍**이 훨씬 정확한 트랙이며 거기서는 accept 경쟁력이 있다.

즉 rebuttal에서 저자가 선택해야 할 것은 "숫자를 늘리는 일"이 아니라 **논문의 계약을
그대로 두고 트랙/프레이밍을 정직하게 맞추거나, 아니면 진짜 실험을 채우거나** 둘 중 하나다.

---

## 1. Paper Summary (리뷰어 요약)

논문은 LLM 생성물 provenance를 토큰 표면이 아니라 **의미 계층**에 싣는 것을 목표로 하는
watermark 전용 semantic IR, *Truthprint*를 제안한다. 핵심 착상은 문장의 진리조건적
내용(개체·술어·의미역·극성·양·시간·귀속 등)을 **locked invariant**로 고정하고, 의미를
바꾸지 않는 실현 자유도(태/절 포장/담화 연결어/어순 등)만을 **carrier**로 사용해
비밀키 기반으로 payload 심볼을 싣는 것이다. Payload는 `p = m ∥ MAC_K(m ∥ n ∥ h_I)`로
인증되고 GF(2) 소거정정 코드로 보호되며, 검출은 재파싱→불변량 정규화→키맵 역산(불확실
carrier는 erasure)→ECC 복호→MAC 검증 순으로 동작한다.

기여는 세 가지로 압축되어 있다: (1) field-level mutability 계약으로서의 method,
(2) validator soundness를 명시적으로 가정한 조건부 분석(보호필드 fidelity, fresh-payload
unforgeability의 EUF-CMA 환원, per-test 태그 수용확률 2^-τ), (3) 재현 가능한 Stage-1
증거(암호·코딩 코어 P1–P4, 폐쇄도메인 언어 왕복 L1–L3)와 반증 가능한 평가 프로토콜.
논문은 다국어 translation/paraphrase 강건성을 **"미검증(Not established)"** 으로
명시적으로 분류하고, 번역 표는 실제 번역이 아닌 **진단용 시뮬레이션**임을 반복해서 밝힌다.

**검증 결과(리뷰어가 직접 실행함):** 참조 구현과 논문 표의 수치는 일치한다.
`truthprint selftest` PASS, `truthprint_poc.py`에서 P1–P4 재현(20,000 docs에서 위양성
0, per-test bound 2.33×10⁻¹⁰), `eval_baselines.py`에서 Table V/VI 수치 재현. 즉 논문이
"측정했다"고 주장하는 범위 안에서는 재현성이 실제로 높다.

---

## 2. ARR 축별 점수

| ARR 축 | 점수 | 근거 |
|---|---:|---|
| **Soundness** | 3.0/5 | 조건부 정리들은 수학적으로 타당하고 코어 검증은 재현된다. 그러나 논문의 중심 가치 명제("의미 계층에 실으면 번역·패러프레이즈에 강건")는 아직 **자연어 파이프라인에서 증명되지 않았고**, 가장 강한 가정(validator/parser soundness)이 곧 미해결 연구문제와 동치다. |
| **Excitement** | 3.5/5 | "무엇이 절대 바뀌면 안 되는가"를 embedding 거리 대신 typed predicate로 명시하고 MAC로 provenance를 인증한다는 관점은 NLP·보안 독자 모두에게 신선하다. 다만 흥분도는 "이게 실제로 되는가"에 대한 증거 부재로 상쇄된다. |
| **Reproducibility** | 4.0/5 (코어 한정) | seed 고정, 표준 라이브러리만 사용, CI, CLI 재현 명령까지 갖췄고 리뷰어 재현에 성공. 단, 재현되는 것은 코딩·암호 코어이지 논문 제목이 약속하는 시스템 성능이 아니다. |
| **Novelty** | 2.5/5 | typed mutability + MAC + ECC + erasure의 결합은 system-level novelty로 유효하나, 각 요소는 기존 구성물이며 결합이 만드는 **새로운 Pareto 개선을 실제 텍스트에서 입증**하지 못했다. |
| **Clarity** | 3.5/5 | claim–evidence table, 조건부 정리 라벨링, 진단 시뮬레이션 disclaimer 등 정직성 장치는 우수. 다만 본문에 roadmap·software skeleton·미래형 방법론이 과다해 핵심 분석·증거를 밀어낸다. |
| **Overall** | **2.5/5** | 좋은 아이디어 + 정직한 서술 + 재현 가능한 코어. 그러나 main track이 요구하는 end-to-end 증거의 부재가 결정적. |

---

## 3. Summary of Strengths

1. **문제 재정의가 정확하다.** "provenance는 내용 정체성의 지속을 주장하는데 carrier는
   언어별 어휘 결정에 의존한다"는 구조적 불일치 진단은 설득력 있고, He et al.(2024)의
   cross-lingual 소거 결과와 잘 맞물린다.
2. **보수적 실패 처리(erasure-first)가 실무적으로 옳다.** 불확실 carrier를 틀린 bit로
   읽지 않고 erasure로 기록하며, 용량 미달 시 attribute 대신 abstain한다. provenance
   시스템에서 요구되는 안전 방향(틀린 귀속보다 무귀속)이 설계에 내장돼 있다.
3. **provenance를 통계 유사도가 아니라 인증으로 다룬다.** `MAC_K(m ∥ n ∥ h_I)`로
   invariant digest에 payload를 바인딩해, "높은 임베딩 유사도"가 아니라 "MAC 검증"을
   귀속 조건으로 삼은 것은 provenance claim을 훨씬 방어 가능하게 만든다.
4. **정직성 인프라가 모범적이다.** Table (Claim–Evidence)에서 Demonstrated /
   Conditional / Not established를 분리하고, 진단 시뮬레이션을 "순위 매김에 쓰지 말라"고
   명시한다. 이는 최근 워터마킹 논문에서 흔한 과대주장 문제를 선제적으로 차단한다.
5. **재현성이 실제로 확인된다.** 리뷰어가 표준 파이썬만으로 P1–P4, L1–L3, Table V/VI를
   재현했고 수치가 원고와 일치했다. Artifact 완성도는 이 분야 평균 이상이다.
6. **위협 모델이 성숙하다.** Kerckhoffs 가정, replay/splicing/nonce discovery/
   detector-oracle을 구분하고, ValidRemoval = (제거 ∧ 의미 보존)로 공격 성공을 정의한
   점은 보안 리뷰어에게 신뢰를 준다.

---

## 4. Summary of Weaknesses (accept를 막는 순서대로)

### W1. 중심 가치 명제가 자연어에서 미검증 — 그리고 그 검증이 곧 이 논문의 난제다 (치명)
보호필드 fidelity 정리는 "sound한 parser/validator"를 가정한다. 그러나 번역·패러프레이즈
뒤 negation scope·attribution·quantity를 정확히 복원하는 sound frontend를 만드는 일이
바로 이 논문이 풀겠다고 한 문제다. 따라서 현재 정리는 **IR 내부 일관성**을 증명할 뿐
자연어 출력의 사실 보존을 증명하지 않는다. main track 리뷰어는 "가정을 성공 조건으로
옮겨 놓았다"고 읽을 것이다.
→ *필요:* field별 extraction P/R, 변환 전후 consistency, human factual-equivalence,
parser-confidence에 따른 fidelity–coverage 곡선. polarity/number/time/attribution/
causality를 절대 하나의 accuracy로 합치지 말 것.

### W2. 핵심 표(번역 강건성)가 실측이 아니라 유도된 시뮬레이션 (치명)
Table (transformed-channel)의 EN→KO/HI 수치는 `τ_tok`, `ε_inv`를 먼저 정한 뒤 각
방법의 생존확률을 **공식으로 유도**한 것이다. 논문이 이를 정직하게 밝히고 있음에도,
표가 본문 결과 위치에 있으면 리뷰어·독자는 이를 실제 성능으로 오독할 위험이 크다.
"token은 붕괴, semantic은 생존"은 실험적 발견이 아니라 채널 정의의 직접적 귀결이다.
→ *권고:* 수치 표는 **appendix/artifact로 이동**하고 본문에는 "시뮬레이터 회귀
테스트"라는 한 문장 포인터만 남길 것. 확보한 공간에 claim–evidence와 실제 오류 사례를 배치.

### W3. 공정한 end-to-end baseline 비교 부재 (치명)
baseline은 원 논문의 실제 생성기·검출기가 아니라 signal-placement proxy이며,
Truthprint만 실제 문장·BLEU를 보고한다. 서로 다른 추상화를 한 표에 놓으면 우열 근거가
되지 못한다. KGW와 SynthID를 한 범주로 묶은 것도 attribution을 흐린다.
→ *필요:* MarkLLM 등 공개 toolkit 또는 공식 구현으로 동일 LLM·prompt·길이·decoding
예산에서 실행, SemStamp/SIR/SWAN/DEW와 실제 공격 출력에서 비교, 모든 방법에 동일 quality/latency 지표.

### W4. novelty가 상호작용이 아니라 구성요소 나열로 읽힌다 (중대)
typed schema·MAC·ECC·semantic carrier는 각각 알려진 아이디어다. accept를 위해선
"결합이 만드는 새 성질"을 최소대조쌍으로 보여야 한다. 어떤 현상에서 SWAN/embedding이
실패하고 Truthprint가 성공하는지에 대한 실제 결과가 없다.
→ *필요:* negation/number/temporal/modality/attribution/causal 별 challenge set +
ablation(full / no-validator / embedding-only validator / no-MAC-binding / no-ECC /
structure-only)을 동일 FPR·생성 예산에서.

### W5. 시스템-수준 FPR과 nonce 해석 프로토콜 (중대)
2^-τ는 이상화된 단일 후보의 태그 통과 확률일 뿐, parser가 여러 payload·nonce·key를
탐색하면 union bound의 시험 횟수가 필요하다. 논문은 이를 분리해 서술하지만, **후보
key–nonce 수에 따른 실제 latency와 FPR 예산**은 측정되지 않았다. nonce가 out-of-band로
주어진다는 전제도 배포 현실성(등록소·시간버킷 탐색)에 대한 정량 평가가 없다.
→ *필요:* nonce discovery 비용, key rotation/retention, 후보 수 대비 system FPR 곡선.

### W6. ACL 형식·페이지 예산 부적합 (형식, 그러나 실질적)
현재 본문은 광범위한 background, Prototype Roadmap, 상세 software skeleton, 미래형
Experimental Methodology를 포함해 ACL 8쪽 본문 예산을 크게 초과할 가능성이 높다.
→ *권고:* roadmap·architecture·data-model listing·진단 시뮬레이션 표를 appendix로
이동하고, 본문은 (문제→계약→인코더/검출기→조건부 분석→확보한 Stage-1 증거→실제 실험)
순으로 재편. 확보 공간을 실측 결과에 사용.

### W7. "language-neutral / translation-robust" 어휘가 여전히 기대를 과설정 (중간)
제목이 "Designing …"으로 완화됐고 본문 disclaimer도 충실하나, 초록·키워드·표 캡션의
"translation robustness"·"language-neutral" 어휘는 리뷰어의 기대를 실측 결과 쪽으로
당긴다.
→ *권고:* 초록에서 이들을 일관되게 *design objective / intended interface*로 한정하고,
"현 프론트엔드는 폐쇄도메인 영어 템플릿"임을 초록 안에서 한 번 더 못박을 것.

---

## 5. Comments, Suggestions, Questions (저자에게)

- **Q1 (트랙 선택):** 저자는 이 논문을 (a) end-to-end 실험을 붙여 main track SOTA로
  갈 것인지, (b) 지금의 설계+검증+프로토콜 정체성을 유지해 Findings/워크숍으로 갈
  것인지 rebuttal에서 명확히 해달라. 두 경로는 서로 다른 문서를 요구한다.
- **Q2:** L2에서 19/64 carrier가 소거됐다고 하는데, 이 소거율은 실제 rewrite에서
  *측정된* 것인가 아니면 주입된 것인가? 실제 rewrite라면 rewrite 규칙 집합과 그
  대표성을 밝혀달라.
- **Q3:** `InvariantEq`가 hard field에서 symbolic로 판정된다면, soft invariant(강조·
  화용적 함의)에서의 오분류가 fidelity와 capacity에 미치는 영향을 정량화할 수 있는가?
- **Q4:** SWAN(AMR 반송)과의 최소대조쌍 하나라도 실제 문장에서 제시 가능한가? "mutability
  typing이 있어서 SWAN이 놓치는 X를 잡는다"의 X를 구체 예로.
- **제안:** claim–evidence table을 논문 앞쪽(Introduction 직후)에 두고, 모든 정리·표
  캡션이 그 표의 행을 참조하도록 상호링크하면 오독 위험이 크게 준다.
- **제안:** 진단 시뮬레이션 표를 남긴다면 캡션 첫 줄을 "This is a simulator regression
  test, not a method comparison"으로 시작해 시선의 첫 접점에서 오독을 차단.
- **미세:** `selftest` CLI는 5,000 docs(상한 6.0×10⁻⁴), `truthprint_poc.py`는
  20,000 docs(상한 1.5×10⁻⁴)를 쓴다. 본문 수치(20,000)와 CLI 기본값의 차이를 각주로
  밝히면 재현자가 혼동하지 않는다.

---

## 6. Reproducibility (리뷰어 실행 로그 요약)

| 항목 | 결과 |
|---|---|
| `truthprint selftest` | PASS (P1–P4, L1–L3) |
| `paper/reference/truthprint_poc.py` | P1–P4 재현, 20k docs 위양성 0, per-test bound 2.33×10⁻¹⁰ |
| `code/scripts/eval_baselines.py` | Table V/VI 수치 재현 |
| 참조 구현 ↔ 논문 표 | **일치** |

→ 논문이 "측정했다"고 명시한 범위의 재현성은 우수. 이 점은 accept 근거는 못 되지만
논문의 정직성을 강하게 뒷받침하며, camera-ready 시 artifact badge 대상이 될 수 있다.

## 7. Ethical Concerns

명시적 우려 없음(합성 템플릿, 개인정보·인간피험자·모델추론 없음). Ethics 절이
오탐 오남용·false accusation·dual-use·payload에서 개인정보 배제를 이미 다룬다. EU AI
Act를 준수 보장이 아닌 동기로만 인용한 것도 적절.

---

## 8. Accept로 가는 최소 실험 패키지 (main track 경로)

1. 실제 LLM 2종 + MT 2종 + 최소 3개 언어쌍(EN·KO·HI 축, 가능하면 ZH/AR)에서
   생성→번역/패러프레이즈→재파싱→검출까지 end-to-end.
2. 공식/검증된 baseline 구현과 동일 생성·품질 예산, KGW와 SynthID 분리.
3. 문서 단위 held-out calibration, TPR@{1, 0.1, 0.01}%FPR + bootstrap 95% CI.
4. field별 challenge set + human factual-equivalence 기반 frontend 평가.
5. replay/splicing/adaptive removal/nonce-search 실험과 system FPR·latency 곡선.
6. full-component ablation과 capacity/abstention/length 곡선.

## 9. 실험 없이 지금 accept 가능성을 높이는 최소 편집 (Findings/워크숍 경로)

- 진단 시뮬레이션 표를 appendix로 이동, 본문은 한 문장 포인터.
- roadmap·software skeleton을 appendix로 이동, 본문을 8쪽 예산에 맞게 재편.
- 초록·키워드·캡션의 robustness/language-neutral 어휘를 design objective로 일관 한정.
- claim–evidence table을 앞쪽으로 이동하고 전 절에서 상호참조.
- 제목 부제를 "a design and verified coding core with a falsifiable evaluation
  protocol"에 가깝게 조정해 정체성을 첫 줄에서 확정.

---

## 10. 최종 권고

- **ACL 2027 main, long paper, 현 상태:** Reject / Weak Reject. 이유는 품질이 아니라
  **증거–주장 간극과 트랙 불일치**.
- **Findings of ACL 또는 TrustNLP/워터마킹 워크숍, 현 상태 + 9절 편집:** Accept 가능.
  정직한 설계 프레임 + 재현 가능한 코어 + 사전등록 프로토콜은 이 트랙들의 가치와 부합.
- **ACL 2027 main + 8절 실험:** Borderline Accept 이상 진입 가능. novelty가 2.5/5
  수준이어도 중요성·실증성·재현성의 결합으로 경쟁력 확보.

가장 중요한 메시지는 앞 두 리뷰와 같되 한 걸음 더 나아간다: **이 논문의 결함은
"설명 부족"이 아니라 "증거 부족"이며, 동시에 "정체성 오배치"다.** 저자가 진짜 실험을
채우거나(→main), 정체성을 정직하게 재배치하면(→Findings/워크숍), 두 경로 모두에서
accept은 현실적이다. 표현만 손질해 main track 점수를 올리려는 시도는 권하지 않는다.
