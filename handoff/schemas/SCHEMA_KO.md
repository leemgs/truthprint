# 핸드오프 파일 스키마 (필드 정의)

`handoff/validate_handoff.py`가 이 정의대로 검사합니다. enum 값은 정확히 지켜 주세요.

## 공통 enum (불변량 필드)
- `polarity`: `positive` | `negative`
- `time_dir`: `previous` | `following`  (기준일 이전/이후)
- `modality`: `asserted` | `necessary` | `possible`
- `attribution`: `none` | `report` | `vendor`
- `causation`: `none` | `cause` | `purpose`
- `quantity`: 정수 (예: 1, 2, 3, 5)
- `agent`, `patient`, `predicate`: 문자열 (predicate는 현재 폐쇄도메인에서 `FIX`)

## 01_source_items.jsonl  *(Claude 제공 — 당신은 번역 대상 원문으로 사용)*
| 필드 | 타입 | 설명 |
|---|---|---|
| `doc_id` | str | 문서 ID |
| `split` | str | `test` \| `calibration` |
| `lang_src` | str | 원문 언어 (예: `en`) |
| `domain` | str | 도메인 (예: `news`) |
| `scheme`,`key_id` | str | 워터마크 스킴/키 ID (**변경 금지**) |
| `nonce_hex` | str(hex) | 문서 nonce (**변경 금지**) |
| `message_bits` | str | 삽입 메시지 비트열 (**변경 금지**) |
| `code` | obj | `{n,k,msg_len,tag_bits}` |
| `facts` | list | 문장별 불변량(+`sent_id`) |
| `watermarked_text` | obj | `{sent_id: 영어 원문}` — **이걸 번역/변형하세요** |

## 02_transformations.jsonl  *(당신 작성 — 필수)*
| 필드 | 타입 | 설명 |
|---|---|---|
| `transform_id` | str | 변환 1건당 고유 ID |
| `doc_id`,`sent_id` | str | 01의 항목을 가리킴 |
| `transform_type` | enum | `translation` \| `roundtrip_translation` \| `paraphrase` \| `summarization` \| `adaptive_paraphrase` \| `splice` \| `noop` |
| `direction` | str | 예: `en->ko`, `en->ko->en` |
| `system` | str | **실제 사용 시스템 이름+버전** (`REPLACE...` 금지) |
| `params` | obj | 온도/강도/압축률 등 |
| `output_text` | str | **실제 변환 결과 문장** |
| `round_trip` | bool | round-trip 여부 |

## 03_annotations.jsonl  *(당신 작성 — 필수, 논문의 frontend)*
| 필드 | 타입 | 설명 |
|---|---|---|
| `transform_id` | str | 02의 항목을 가리킴 |
| `annotator_id` | str | 주석자 (2명 이상 권장) |
| `invariants_observed` | obj | 변환문에서 사람이 읽은 불변량 6필드(+agent/patient/predicate/quantity) |
| `carriers_observed` | list | `[{carrier, value, reliable}]` |
| `carrier` | enum | `voice` \| `time_position` |
| `value` | enum | voice: `active`\|`passive`, time_position: `front`\|`end` |
| `reliable` | bool | 관측 신뢰 여부 (false면 검출 시 erasure로 처리) |
| `invariant_preserved` | bool | 변환이 의미(불변량)를 보존했는가 |
| `notes` | str | 자유 서술 |

## 04_human_factuality.csv  *(당신 작성 — 권장)*
헤더: `pair_id,doc_id,sent_id,transform_id,kind,field_if_altering,human_equivalent,annotator_id,notes`
- `kind`: `benign` | `altering`
- `field_if_altering`: altering일 때 바뀐 필드명(예: `polarity`)
- `human_equivalent`: `1`(의미 동일) | `0`(다름)

## 05_baseline_outputs.jsonl  *(당신 작성 — 선택)*
| 필드 | 타입 | 설명 |
|---|---|---|
| `method` | str | 예: `SynthID-Text`, `SemStamp`, `SWAN`, `DEW` |
| `doc_id` | str | 01의 문서 |
| `condition` | str | `clean`, `en->ko` 등 |
| `score` | number | 검출 점수 |
| `decision` | str | `watermarked` \| `not_watermarked` |
| `fpr_operating_point` | number | 임계값 기준 FPR (예: 0.01) |
| `impl` | str | 사용한 공식 구현/커밋 |

## split.json
`{"calibration": [doc_id...], "test": [doc_id...]}` — 두 그룹은 겹치면 안 됩니다.
