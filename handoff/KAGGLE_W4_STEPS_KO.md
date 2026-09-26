# W4 baseline 비교 — Kaggle/Colab 복사·붙여넣기 절차

주 트랙 최대 관문(W4): **공식/실제 baseline을 동일 real-MT 파이프라인에 돌린 head-to-head
비교**. GPU가 필요해 저자 환경에서 실행합니다. 사람 주석은 필요 없습니다.

## 절차 (약 10–20분, GPU T4)
1. Kaggle → **New Notebook** (또는 Colab). Settings에서
   - **Internet: On**
   - **Accelerator: GPU T4**
2. 이 저장소의 `handoff/Truthprint_W4_Baselines_Kaggle.ipynb`를 업로드하거나,
   첫 셀에 아래를 붙여넣어 클론:
   ```python
   !git clone --depth 1 https://github.com/leemgs/truthprint /kaggle/working/truthprint
   ```
   그런 다음 노트북 파일을 열어 **Run All**.
3. 마지막 셀이 `w4_results.zip`을 만듭니다. 다운로드해서 저에게 전달하세요.

## zip 안에 들어오는 것
- `05_baseline_outputs.jsonl` — 실제 검출기 점수 (KGW 보장, 가능하면 SynthID/SIR).
- `baselines_real.md` / `.json` — 채점된 head-to-head 비교표 (TPR@1%FPR + AUC).
- `provenance.json` — 같은 소스에 대한 Truthprint 의미기반 provenance 실측.

## 제가 zip을 받으면
- `eval_baselines_real.py`로 재채점해 CI를 확정하고,
- 논문 §Experimental Methodology에 **실데이터 비교표**(진단 시뮬레이션을 대체)를
  추가합니다. 이때 Table 5/6 진단 시뮬레이션은 이미 부록으로 내려가 있으므로,
  본문에는 이 실측 비교만 남습니다.

## 조절 포인트
- `N_DOCS`(Cell 2): 문서 수. 많을수록 CI가 좁아짐(50 권장, GPU면 빠름).
- `MODEL_ID`(Cell 3): 기본 `gpt2`. 더 유창한 텍스트가 필요하면 instruct 모델로 교체
  (예: `Qwen/Qwen2.5-0.5B-Instruct`). 워터마크 생존성 결론은 모델과 무관.
- MarkLLM(Cell 5): 설치·API가 버전에 따라 다를 수 있음. 실패해도 KGW 결과는 보존됨.
  SynthID/SIR가 꼭 필요하면 실패 메시지를 저에게 알려주세요 — 해당 버전에 맞춰
  호출을 고쳐 드립니다.

## 왜 이게 W4를 닫나
- 논문의 진단 시뮬레이션(Appendix A)은 "순위 매기지 말 것"이라 명시된 **proxy**였습니다.
- 이 절차는 **실제 LLM 생성 → 실제 KGW 워터마크 → 실제 NLLB 번역 → 실제 z-score 검출**로
  토큰-레벨 신호가 번역에서 붕괴함을 실측하고, 동일 파이프라인의 Truthprint 의미기반
  provenance 생존율과 **같은 operating point에서** 나란히 비교합니다 — 리뷰어가 요구하는
  apples-to-apples 실데이터 비교.
