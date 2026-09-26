# W5 neural 파서 — Kaggle/Colab 복사·붙여넣기 절차

주 트랙 W5: 어휘집을 **wide-coverage neural 파서**로 대체하고, 동일 real-MT 번역과
개방 도메인 문장에서 어휘집과 head-to-head 비교. GPU가 필요해 저자 환경에서 실행합니다.
사람 주석은 필요 없습니다(open-domain gold 6문장 내장).

## 절차 (약 10–20분, GPU T4)
1. Kaggle → New Notebook (또는 Colab). Settings:
   - **Internet: On**
   - **Accelerator: GPU T4**
2. `handoff/Truthprint_W5_NeuralParser_Kaggle.ipynb`를 업로드하거나 첫 셀에서 클론:
   ```python
   !git clone --depth 1 https://github.com/leemgs/truthprint /kaggle/working/truthprint
   ```
   노트북을 열고 **Run All**.
3. 마지막 셀이 `w5_results.zip`을 만듭니다. 다운로드해 저에게 전달하세요.

## zip 내용물
- `neural_parser_outputs.jsonl` — 문장별 gold + neural 예측.
- `neural_parser.md` / `.json` — 필드별·도메인별 복원율 + lexicon vs neural 비교표.

## 제가 zip을 받으면
- `eval_neural_parser.py`로 재채점(CI 확정) 후, 논문 §Stage-2 절에 **neural 파서의
  개방 도메인 복원율**을 추가하고, "wide-coverage 파서는 다음 단계"라는 문장을
  실측 결과로 갱신합니다.

## 조절 포인트
- `LLM_ID`(Cell 4): 기본 `Qwen/Qwen2.5-1.5B-Instruct`. 더 크게(정확도↑) 또는 더 작게
  (속도↑) 교체 가능. instruct 계열이면 무엇이든 동작(백엔드는 `fn(prompt)->str`).
- 개방 도메인 문장 수(Cell 2 `OPEN`): 늘리면 개방 도메인 CI가 좁아집니다. 문장·gold를
  추가하고 요청 주시면 됩니다.
- Cell 2의 `template`/`open` 비율로 폐쇄 vs 개방 대비를 조절.

## 왜 이게 W5를 닫나
- 논문의 Stage-2는 **lexicon**이라 폐쇄 도메인에 한정됩니다(리뷰 W5).
- 이 절차는 동일 드롭인 인터페이스의 **neural 파서**를 실제 LLM으로 돌려, 어휘집이
  무너지는 개방 도메인에서의 복원율을 실측합니다 — provenance/authentication 코드는
  그대로 두고 프론트엔드만 교체(`truthprint.neural_parser.NeuralInvariantExtractor`).
