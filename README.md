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

예측 플랫폼 자동 업데이트: [한 번 실행·24시간 스케줄러·WSL cron 설정](docs/AUTOMATIC_UPDATES.md)

무료 공개 배포: [Render 무료 주소와 GitHub Actions 자동 갱신](docs/FREE_DEPLOYMENT.md)

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

3개월 뒤 금리 방향(`인하·동결·인상`) 분류 모델 평가:

```bash
python -m ml.classify_rate_direction
python -m ml.compare_direction_models
python -m ml.post_pandemic_forecast
python -m ml.tune_post_pandemic_models
python -m ml.reliability_forecast
```

분류 모델은 세 방향의 확률을 `outputs/live_prediction.json`에 저장하고,
`outputs/live_prediction_dashboard.png`에서 막대그래프로 보여준다. 이 확률은
아직 확률 보정(calibration)을 거치지 않은 학습용 결과이므로 실제 발생확률로
단정하면 안 된다.

두 번째 명령은 항상 동결 Baseline, Logistic Regression, Random Forest,
XGBoost를 동일한 시간순 테스트 구간에서 비교한다.

세 번째 명령은 2022년 이후 포스트 팬데믹 데이터만 사용하고, 3개월
목표값 누수를 막은 순차 검증과 최신 3개월 방향 예측을 실행한다.

네 번째 명령은 물가·환율·국고채 금리의 시차 변화, 한미 금리 차,
채권–정책금리 차와 최근 금리 방향을 추가한다. `TimeSeriesSplit` 안에서
Random Forest와 XGBoost 설정을 조정하고 방향별 탐지율도 출력한다.

다섯 번째 명령은 2008년 이후 데이터, 최근 관측치 가중치, 변경/동결과
인하/인상의 2단계 분류, 중첩 시계열 검증을 적용해 Baseline 대비 정확도,
Macro F1과 Brier Score를 함께 평가한다.

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

- 홈(현재 예측 요약): `http://127.0.0.1:8000`
- 학습 센터: `http://127.0.0.1:8000/learn`
- 모델·검증: `http://127.0.0.1:8000/model`
- 프로젝트 인사이트: `http://127.0.0.1:8000/insight`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## 엔드포인트

- `GET /health`: 서버 상태 확인
- `GET /forecast/latest`: 최신 3개월 금리 방향과 모델 결과
- `GET /forecast/reliability`: 신뢰도 개선 데이터 설계 실험
- `GET /forecast/history`: 최근 월별 기준금리와 경제지표
- `GET /forecast/status`: 자동 업데이트 실행 상태
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
