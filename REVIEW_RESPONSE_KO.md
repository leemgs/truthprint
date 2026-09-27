# ACL 리뷰 대응 종합 (W1–W6)

이 문서는 ACL(주 트랙) 리뷰에서 제기된 약점 W1–W6(및 C2)에 대해 **무엇을 어떻게
반영했는지**, **근거 수치와 위치**, **정직한 한계**를 한 곳에 정리한 기록입니다.
모든 변경은 이미 `main`에 병합돼 있습니다. 전체 코드 diff는 아래 compare 링크에서
확인할 수 있습니다.

- 저장소: `leemgs/truthprint`
- 전체 변경 비교(리뷰 시작 전 → 현재):
  https://github.com/leemgs/truthprint/compare/75f95ef...main

---

## 요약 표

| # | 리뷰 약점 | 대응 유형 | 근거·수치 | 논문 위치 |
|---|---|---|---|---|
| W1 | 초록이 realization-carrier와 meaning-digest 두 메커니즘을 혼동 | 원고 수정 | 표제 메커니즘(carrier)은 실제 MT에서 음성(0/192), 생존한 것은 meaning-digest임을 명시 분리 | Abstract |
| W2 | 의미-수준 FP(contract collision) 미측정 | **실측** | core6 충돌 floor $5.2\times10^{-3}$(≈1/192) = 보고된 FP와 일치, $2^{-32}$의 $2\times10^{7}$배 | `sec:provenance`, Table 1, `paper/results/semantic_fp.md`, `truthprint.semantic_fp` |
| W3 | 검증기 건전성(Assumption 1)이 미검증 가정 | **실측 명시** | 검증기 false-accept율: 폐쇄도메인 0(C1), 실제 MT ≤0.01(tamper rejection ≥0.99) | Prop 1 직후 문단, Table 1 |
| W4 | 공식 baseline과 동일조건 실데이터 비교 부재 | **실측(Kaggle GPU)** | 실제 KGW 토큰 워터마크 clean 0.960 → 번역 0.000–0.380 붕괴, meaning-digest 0.502–0.980 생존 | `sec:baselines`, Table `tab:baselines`, Table 1, Abstract, `paper/results/baselines_real.md` |
| W5 | Stage-2가 lexicon(폐쇄도메인)뿐, wide-coverage 아님 | **실측 파일럿(LLM-MT)** | 개방 도메인에서 neural 0.614 > lexicon 0.481(어휘집 붕괴 지점); 폐쇄는 lexicon 우위 | `sec:neural`, Table 1, `paper/results/neural_parser.md`, `truthprint.neural_parser` |
| W6 | 본문이 ACL 8쪽 예산 초과(구현·로드맵 과다) | 원고 재구성 | 진단 시뮬레이션·재현성·아키텍처·로드맵·평가 프로토콜을 부록 A–E로 이동 | Appendices A–E |
| C2 | 진단 시뮬레이션 표가 오독 위험 | 원고 재구성 | Table 5/6를 부록 A로 이동, 본문엔 "순위 매기지 말 것" 경고 포인터만 | `app:diagnostic` |

---

## 상세

### W1 — 초록 메커니즘 분리
초록이 (i) 실현 자유에 페이로드를 심는 **realization-carrier**(실제 NLLB 번역에서 표면
파서 0/192 = 정직한 음성)와 (ii) 불변자 다이제스트에 키 태그를 등록하는 **meaning-digest**
(번역 생존)를 명시적으로 구분하도록 재작성.

### W2 — 의미-수준 FP 실측
meaning-digest는 복원된 contract가 태그를 재생하면 인증되므로, 저엔트로피 contract를
공유하는 서로 다른 문서가 암호 태그 이전에 충돌한다. 폐쇄도메인 contract 공간을 열거해
충돌 floor를 계산: core6 = 192개(7.6비트) → $5.2\times10^{-3}$. 이는 보고된 FP
0.001–0.010과 일치하며 $2^{-32}$가 아니라 **contract 엔트로피**가 FP를 지배함을 증명.
(`code/truthprint/semantic_fp.py`, `code/scripts/eval_semantic_fp.py`, 테스트 포함)

### W3 — 검증기 건전성 경험적 명시
Prop 1의 하중 가정(Assumption 1)을 **false-accept율**로 측정: 폐쇄도메인 tamper 탐지
1.000(오수용 0, C1), decode-only ablation 0.000(건전성은 재추출이 공급, C2), 실제 MT
tamper rejection ≥0.99. wide-coverage 건전성은 open으로 유지 → Prop 1은 조건부.

### W4 — 실제 baseline head-to-head (Kaggle GPU)
자체 완결형 KGW(logit 조작, gpt2) 임베딩 → 실제 NLLB-200-distilled-600M 6개 조건 번역
→ z-score 검출(1% FPR 보정). 동일 파이프라인의 meaning-digest와 비교.
토큰 워터마크는 clean에서만 탐지(0.960), 번역 후 붕괴(0.00–0.38); meaning-digest는
생존(0.50–0.98). 진단 시뮬레이터(부록)를 대체하는 실데이터 비교.
(`code/scripts/eval_baselines_real.py`, `handoff/Truthprint_W4_Baselines_Kaggle.ipynb`)

### W5 — wide-coverage neural 파서 파일럿 (실제 LLM-MT)
lexicon과 동일 인터페이스의 neural 추출기(`truthprint.neural_parser`)를 무료 호스팅
모델로 실행: 16문장(폐쇄 10 + 개방 6)을 6개 조건으로 실제 기계번역 후 재파싱(96문장).
**개방 도메인에서 neural 0.614 > lexicon 0.481**(어휘집이 무너지는 지점), 폐쇄 템플릿은
lexicon 우위(0.970 vs 0.726). 정직한 한계: 소규모, 단일 모델이 번역·추출 겸함, 독일어
번역 형식 실패로 제외, NLLB 아닌 LLM-MT.
(`code/scripts/eval_neural_parser.py`, `handoff/Truthprint_W5_NeuralParser_Kaggle.ipynb`)

### W6 — 본문 8쪽 재구성
구현 세부·future-work를 부록으로 이동: A(진단 시뮬레이션), B(재현성·표기), C(소프트웨어
아키텍처), D(프로토타입 로드맵), E(확장 평가 프로토콜). 본문은 16개 섹션으로 축소하고
연구질문·평가 매트릭스는 유지. `pdflatex`가 이 환경에 없어 **저자가 로컬 `make acl`로
8쪽 이내 최종 확인** 필요.

---

## 재현
```bash
cd code && pip install -e ".[dev]" && pytest -q            # 66 tests
python3 scripts/eval_semantic_fp.py --out ../paper/results # W2
python3 scripts/eval_challenge.py                          # C1–C3 (W3)
# W4/W5는 GPU/무료 API 필요 — handoff 노트북 참조
```

## 남은 확장 (선택, 크레딧/GPU 확보 시)
- W4: SynthID/SemStamp/SWAN 공식 구현 추가(현재 단일 KGW baseline).
- W5: 규모 확대 + 번역기≠추출기 분리(현 파일럿은 단일 모델), 독일어 포함.
- 문서 수·언어 확대로 문서-단위 CI 축소.
