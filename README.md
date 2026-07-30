# FastAPI Full Stack

상세 학습 노트: [WSL부터 FastAPI·Swagger·GitHub까지](docs/DEVELOPMENT_STACK_NOTES.md)

금리 예측 입문 노트: [목표 설정부터 모델 검증과 API 설계까지](docs/INTEREST_RATE_FORECASTING_NOTES.md)

첫 실습: [연습용 금리 데이터와 Baseline](docs/BASELINE_EXERCISE.md)

두 번째 실습: [Baseline과 Linear Regression 비교](docs/MODEL_COMPARISON_EXERCISE.md)

모델 비교 그래프 생성:

```bash
python -m ml.visualize_comparison
```

실제 데이터 자동 수집: [ECOS 인증키 설정과 통계표 탐색](docs/REAL_DATA_AUTOMATION.md)

ECOS 실제 데이터 수집:

```bash
python -m data_pipeline.collect_ecos_data
```

이 수집 과정은 FRED의 `FEDFUNDS` 월별 미국 금리도 함께 병합합니다.

> This product uses the FRED® API but is not endorsed or certified by the
> Federal Reserve Bank of St. Louis.

실제 데이터 모델 비교:

```bash
python -m ml.compare_real_models
```

현재 월 잠정 데이터와 시험 예측:

```bash
python -m data_pipeline.collect_live_features
python -m ml.predict_live
python -m ml.visualize_live_prediction
```

## 구조

```text
main.py        FastAPI 실행 진입점
backend/       FastAPI 백엔드
frontend/      HTML, CSS, JavaScript 프론트엔드
.env           로컬 API 키
```

## 실행

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn main:app --reload
```

서버 실행 후 아래 주소를 사용할 수 있습니다.

- 프론트엔드: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## 엔드포인트

- `GET /health`: 서버 상태 확인
- `GET /users`: 전체 사용자 조회
- `GET /users/{user_id}`: 사용자 단건 조회
- `POST /users`: 사용자 등록
- `POST /chat`: OpenAI Responses API 호출

`POST /chat` 요청 예시:

```json
{
  "message": "안녕! 한 문장으로 자기소개해줘."
}
```
