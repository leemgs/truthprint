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

## 무료 API로 실행 (GPU 불필요, 권장)
Cell 4는 기본으로 **OpenAI 호환 무료 API**를 씁니다(파서는 구조화 추출이라 호스팅 모델로
대체해도 결과 타당성 동일). 무료 제공자 중 하나의 키를 발급받아 넣으세요:
- OpenRouter: `BASE=https://openrouter.ai/api/v1`, `MODEL=meta-llama/llama-3.3-70b-instruct:free`
- Groq: `BASE=https://api.groq.com/openai/v1`, `MODEL=llama-3.3-70b-versatile`
- Gemini(OpenAI 호환): `BASE=https://generativelanguage.googleapis.com/v1beta/openai`, `MODEL=gemini-2.0-flash`

설정법(둘 중 하나):
```python
import os
os.environ['TRUTHPRINT_API_KEY']='<발급받은 무료 키>'
os.environ['TRUTHPRINT_API_BASE']='https://openrouter.ai/api/v1'
os.environ['TRUTHPRINT_API_MODEL']='meta-llama/llama-3.3-70b-instruct:free'
```
또는 Cell 4 상단 `API_KEY/BASE/MODEL`을 직접 편집. 이 경로면 **GPU 없이 노트북/로컬에서**
실행됩니다(번역 NLLB-600M도 소형이라 CPU로 수 분). 로컬 모델을 쓰려면 Cell 4의
`USE_API=False`로 바꾸세요(그땐 GPU 권장).

## 조절 포인트
- 무료 API 모델 교체: `TRUTHPRINT_API_MODEL`(또는 Cell 4 `MODEL`). instruct 계열 권장.
- 로컬 모드(`USE_API=False`)의 `LLM_ID`: 기본 `Qwen/Qwen2.5-1.5B-Instruct`, 교체 가능.
- 개방 도메인 문장 수(Cell 2 `OPEN`): 늘리면 개방 도메인 CI가 좁아집니다. 문장·gold를
  추가하고 요청 주시면 됩니다.
- Cell 2의 `template`/`open` 비율로 폐쇄 vs 개방 대비를 조절.

## 왜 이게 W5를 닫나
- 논문의 Stage-2는 **lexicon**이라 폐쇄 도메인에 한정됩니다(리뷰 W5).
- 이 절차는 동일 드롭인 인터페이스의 **neural 파서**를 실제 LLM으로 돌려, 어휘집이
  무너지는 개방 도메인에서의 복원율을 실측합니다 — provenance/authentication 코드는
  그대로 두고 프론트엔드만 교체(`truthprint.neural_parser.NeuralInvariantExtractor`).
