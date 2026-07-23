# Presentation Materials — Truthprint

This directory contains slide decks for presenting the Truthprint research to different
audiences.

## Files

| File | Language | Format | Audience |
|---|---|---|---|
| `truthprint_presentation_ko_20260723.pptx` | 한국어 | 12-slide deck | Team / internal sharing |
| `truthprint-poster-en-1page.pptx` | English | 1-page poster (40 × 30 in) | Conference / research venue |

---

## `truthprint_presentation_ko_20260723.pptx` — Korean presentation deck

**Purpose:** Internal sharing and team briefing on the Truthprint research idea.

### Slide outline

| # | Section | Key message |
|---|---|---|
| 1 | Title | 번역·패러프레이즈에도 지워지지 않는 AI 생성 텍스트 출처 워터마킹 |
| 2 | 왜 필요한가 | EU AI Act 제50조 규제 / 모델 붕괴 위험 / 기존 방식의 한계 |
| 3 | 핵심 아이디어 | 토큰이 아니라 '의미(불변식)'에 워터마크를 새긴다 |
| 4 | 동작 방식 | 인코딩 5단계 + 탐지 5단계 파이프라인 |
| 5 | 왜 강건한가 | 번역·패러프레이즈는 ECC로 복구; 의미 훼손은 MAC 실패로 차단 |
| 6 | 형식적 보장 | Thm. 1 위조 불가, Thm. 2 오탐 상한 2⁻ᵗᵃᵘ, Prop. 2 소거 절벽 |
| 7 | 구현·검증 | P1–P4 + L1–L3 속성, 15/15 테스트 통과, 소거율 vs 복구율 표 |
| 8 | 기존 방식과 차이 | 토큰 통계 / 임베딩 방식 대비 반송파·강건성·귀속 판정 비교 |
| 9 | 실용성 | LLM 재학습 불필요, 인라인/비동기 배포, 단락별 위치 확인 |
| 10 | 한계·로드맵 | Stage-1 한정 파서 / 고차수 캐리어 / 다국어 인터링구아 확장 |
| 11 | 참고 자료 | 핵심 참고문헌 목록 |
| 12 | Q&A | — |

---

## `truthprint-poster-en-1page.pptx` — English one-page research poster

**Purpose:** Designed for conference poster sessions (single 40 × 30 in slide,
three-column layout, navy + teal palette).

### Poster sections

| Column | Sections |
|---|---|
| Left | (1) Provenance is now a compliance property — (2) Core idea: lock meaning, carry signal in realization — (3) Formal guarantees |
| Center | (4) Encoding & detection pipeline — (5) Worked linguistic example — (6) Prior-art comparison |
| Right | (7) Verified implementation results — (8) Erasure cliff chart — (9) Scope & next steps |

### Verified results shown

| Property | Result |
|---|---|
| P1 | Exact payload recovery + valid MAC with 28/96 carriers erased |
| P2 | Flipping a locked field (polarity) breaks attribution |
| P3 | 0 / 20,000 false positives at τ = 32 (bound 2.3 × 10⁻¹⁰) |
| P4 | Keyed map is invariant-bound: 43/96 options differ across documents |
| L1–L3 | Sentence-string round-trip: fidelity, recovery (19/64 erased), tamper detection |

---

## Relation to other materials

| Directory | Relation |
|---|---|
| [`paper/`](../paper/) | Full manuscript with formal proofs backing the poster's claims |
| [`code/`](../code/) | Reference implementation that produced the P1–P4 / L1–L3 numbers |
| [`docs/`](../docs/) | Korean-language public homepage built from this presentation content |
| [`patent/`](../patent/) | Patent application preparation materials |
