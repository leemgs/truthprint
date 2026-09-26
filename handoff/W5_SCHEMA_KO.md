# W5 neural 파서 — 데이터 스키마

주 트랙 리뷰 W5("lexicon이 아닌 wide-coverage 파서")를 위한 산출물 스키마.
노트북 `Truthprint_W5_NeuralParser_Kaggle.ipynb`가 아래를 생성하고,
`code/scripts/eval_neural_parser.py`가 채점합니다.

## `neural_parser_outputs.jsonl`
한 줄 = 한 (문장, 조건) 레코드.

| 필드 | 타입 | 의미 |
|---|---|---|
| `sent_id` | str | 문장 식별자 |
| `lang` | str | `en`\|`ko`\|`hi`\|`zh`\|`ar`\|`de` (파서에 넘길 언어) |
| `condition` | str | `clean`\|`rt`\|`ko`\|`hi`\|`zh`\|`ar`\|`de` |
| `domain` | str | `template`(폐쇄 어휘) \| `open`(개방 도메인, out-of-vocabulary) |
| `text` | str | (번역된) 문장 원문 |
| `gold` | dict | 9개 불변 필드의 정답 (agent, patient, predicate, polarity, quantity, time_dir, modality, attribution, causation) |
| `pred` | dict | neural 모델이 추출한 9개 필드 (JSON) |

## 채점기 사용
```bash
python3 code/scripts/eval_neural_parser.py neural_parser_outputs.jsonl --out paper/results
```
출력 `neural_parser.{json,md}`:
- **필드별 복원율**(pred==gold, Wilson CI) 및 all-exact,
- **도메인별**(template vs open) 복원율,
- **lexicon vs neural head-to-head** — 채점기가 동일 `text`에 리포의 어휘집
  추출기(`multilingual.extract_invariants`)를 돌려 두 프론트엔드를 같은 입력에서 비교.

## 핵심: 왜 이게 W5를 닫나
- 어휘집 추출기는 폐쇄 도메인에선 강하지만 개방 도메인 어휘("central bank", "RAISE"
  등)에서 abstain/오독합니다.
- neural 파서(instruct LLM → 9필드 JSON, `truthprint.neural_parser`)는 **동일
  드롭인 인터페이스**(`extract(text,lang)->dict`)라 provenance/authentication 코드를
  바꾸지 않고 교체됩니다.
- 결정적 결과는 `open` 도메인 행: 어휘집이 무너지는 곳에서 neural이 버티면, 논문이
  "다음 단계"로 남겨둔 wide-coverage 파서가 실측됩니다.

## 정직성 노트
- open-domain gold는 노트북에 소량 하드코딩(6문장). 규모를 키우려면 문장·gold를 추가하고
  요청 주세요. 실제 대규모 평가에는 사람 주석(κ 포함)이 권장됩니다(NEXT_STEPS B3).
- `pred`는 모델 출력을 `neural_parser.parse_response`로 정규화한 것이며, 파싱 실패
  필드는 정직하게 `None`(추측 아님)으로 남습니다.
