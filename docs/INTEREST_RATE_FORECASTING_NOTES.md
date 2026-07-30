# 금리 예측 프로젝트 입문 노트

이 문서는 현재 FastAPI 프로젝트를 확장해 **한국은행 기준금리를 예측하는
웹서비스**를 만드는 과정을 공부하기 위한 입문 노트다.

> 금리 예측은 미래를 확정하는 작업이 아니다. 과거 데이터에서 발견한 패턴을
> 바탕으로 가능한 결과와 불확실성을 추정하는 작업이다.

---

## 1. 프로젝트의 전체 목표

최종적으로 다음과 같은 서비스를 만든다.

```text
한국은행·FRED 경제 데이터
        ↓
Python 데이터 수집 및 정리
        ↓
금리 예측 모델 학습
        ↓
FastAPI 예측 API
        ↓
프론트엔드 차트와 예측 결과
```

사용자가 웹 화면에서 예측 기간을 선택하면 다음과 같은 결과를 보여주는 것이
목표다.

```text
현재 기준금리:       2.75%
3개월 후 예상 금리:  3.00%
예상 방향:           인상
예상 범위:           2.50% ~ 3.25%
```

이 숫자는 예시이며 실제 예측 결과가 아니다.

---

## 2. 전체 학습 순서

```text
1. 금리와 경제 데이터 이해
2. 예측 목표 정의
3. 데이터 수집
4. Python으로 데이터 정리
5. 단순한 기준 모델 작성
6. 머신러닝 모델 학습
7. 시간순으로 성능 검증
8. FastAPI 예측 API 제작
9. 프론트엔드에 결과와 차트 표시
10. Git과 GitHub로 변경 이력 관리
```

처음부터 복잡한 인공지능 모델을 사용하지 않는다. 단순한 방법부터 시작해
복잡한 모델이 실제로 더 나은지 단계별로 검증한다.

---

## 3. 무엇을 예측할지 정의하기

“금리를 예측한다”는 표현만으로는 목표가 충분히 명확하지 않다.

다음 항목을 구체적으로 정해야 한다.

### 3.1 금리의 종류

- 한국은행 기준금리
- 미국 연방기금금리
- 국고채 3년 금리
- 국고채 10년 금리
- 은행 예금금리
- 은행 대출금리
- 개인별 예상 대출금리

이 프로젝트의 첫 번째 목표는 다음과 같이 가정한다.

```text
예측 대상: 한국은행 기준금리
예측 시점: 3개월 후
```

### 3.2 예측 기간

같은 금리라도 얼마 뒤를 예측하는지에 따라 문제가 달라진다.

```text
1개월 후
3개월 후
6개월 후
12개월 후
```

일반적으로 예측 기간이 길어질수록 불확실성이 커진다.

---

## 4. 목표값과 입력값

예측 모델에는 목표값과 입력값이 필요하다.

### 4.1 목표값 Target

목표값은 모델이 맞혀야 하는 정답이다.

```text
3개월 후 한국은행 기준금리
```

예를 들어:

```text
현재 기준금리:    2.75%
3개월 후 기준금리: 3.00%
```

이 학습 행에서 모델이 맞혀야 하는 목표값은 `3.00%`다.

머신러닝 코드에서는 목표값을 흔히 `y`라고 표시한다.

```python
y = data["rate_after_3_months"]
```

### 4.2 입력값 Feature

입력값은 모델이 판단에 사용하는 정보다. 머신러닝에서는 feature 또는
설명변수라고 부른다.

사용을 검토할 수 있는 경제지표:

- 현재 한국은행 기준금리
- 소비자물가 상승률
- 근원물가 상승률
- 원/달러 환율
- 실업률
- 경제성장률
- 국고채 3년·10년 금리
- 미국 기준금리
- 가계대출 증가율
- 주택가격 변화율

머신러닝 코드에서는 입력값 묶음을 흔히 `X`라고 표시한다.

```python
features = [
    "current_rate",
    "inflation",
    "exchange_rate",
    "unemployment",
    "us_policy_rate",
]

X = data[features]
```

### 4.3 데이터 표의 예

| 날짜 | 현재 금리 | 물가 | 환율 | 미국 금리 | 3개월 후 금리 |
|---|---:|---:|---:|---:|---:|
| 2025-01 | 3.00 | 2.2 | 1,430 | 4.50 | 2.75 |
| 2025-02 | 2.75 | 2.0 | 1,440 | 4.50 | 2.50 |
| 2025-03 | 2.75 | 2.1 | 1,420 | 4.50 | 2.50 |

마지막 열이 목표값이고, 그 앞의 경제지표가 입력값이다.

위 표의 숫자는 개념 설명용 예시이며 실제 학습 데이터가 아니다.

---

## 5. 회귀와 분류

금리를 다루는 방법은 크게 두 가지다.

### 5.1 회귀 Regression

금리 숫자를 직접 예측한다.

```text
예상 금리: 3.00%
```

연속적인 숫자를 예측하기 때문에 회귀 문제라고 한다.

회귀 모델 예:

- Linear Regression
- Random Forest Regressor
- Gradient Boosting Regressor

### 5.2 분류 Classification

금리의 방향을 범주로 예측한다.

```text
인상
동결
인하
```

정해진 범주 중 하나를 선택하기 때문에 분류 문제라고 한다.

분류 모델 예:

- Logistic Regression
- Random Forest Classifier
- Gradient Boosting Classifier

### 5.3 프로젝트에서 사용할 방식

첫 버전은 다음 정보를 함께 제공하는 방향으로 설계한다.

```text
예상 금리 숫자
+
인상·동결·인하 방향
+
예상 범위
```

예상 방향은 현재 금리와 예상 금리를 비교해 계산할 수도 있다.

```python
def get_direction(current_rate: float, predicted_rate: float) -> str:
    if predicted_rate > current_rate:
        return "인상"
    if predicted_rate < current_rate:
        return "인하"
    return "동결"
```

실제로는 아주 작은 차이를 인상이나 인하로 판단하지 않도록 허용 오차를 둘 수
있다.

---

## 6. Baseline 모델

### 6.1 Baseline이란?

Baseline은 복잡한 모델과 비교하기 위한 가장 단순한 기준 모델이다.

금리는 같은 수준을 유지하는 기간이 많으므로 다음과 같은 모델부터 시작할 수
있다.

```text
3개월 후 예상 금리 = 현재 금리
```

Python 코드:

```python
def predict_baseline(current_rate: float) -> float:
    return current_rate
```

사용:

```python
current_rate = 2.75
prediction = predict_baseline(current_rate)

print(prediction)
```

출력:

```text
2.75
```

### 6.2 단순한 모델이 중요한 이유

머신러닝 모델의 오차가 baseline보다 크다면 복잡한 모델을 사용할 이유가 없다.

```text
Baseline 평균 오차:   0.20%p
머신러닝 평균 오차:   0.30%p
```

위 결과에서는 머신러닝 모델이 더 복잡하지만 성능은 더 나쁘다.

좋은 개발 순서:

```text
Baseline 작성
    ↓
Baseline 성능 측정
    ↓
머신러닝 모델 작성
    ↓
같은 테스트 데이터로 비교
```

---

## 7. 모델 평가

### 7.1 오차 계산

실제 금리가 `3.00%`, 예측 금리가 `2.75%`라면 절대 오차는 다음과 같다.

```text
|3.00 - 2.75| = 0.25%p
```

여기서 `%p`는 퍼센트포인트를 의미한다.

예를 들어 금리가 `2%`에서 `3%`로 바뀌면:

```text
변화량: 1%p
상승률: 50%
```

두 표현은 의미가 다르다.

### 7.2 MAE

MAE는 **Mean Absolute Error**, 즉 평균 절대 오차다.

```python
from sklearn.metrics import mean_absolute_error

actual = [2.50, 2.75, 3.00]
predicted = [2.75, 2.75, 2.75]

mae = mean_absolute_error(actual, predicted)
print(mae)
```

결과가 약 `0.1667`이라면 모델이 평균적으로 약 `0.17%p` 틀렸다는 의미다.

MAE는 단위가 원래 목표값과 같아서 해석하기 쉽다.

### 7.3 방향 정확도

숫자 예측과 함께 인상·동결·인하를 얼마나 정확히 맞혔는지도 측정할 수 있다.

```text
실제 방향: 인하, 동결, 인상, 동결
예측 방향: 인하, 인상, 인상, 동결

정확한 예측: 3개
전체 예측:   4개
방향 정확도: 75%
```

### 7.4 예상 범위

한 개의 숫자만 보여주면 예측이 확실해 보이는 문제가 있다.

```text
예상 금리: 3.00%
```

범위를 함께 제공하면 불확실성을 더 잘 표현할 수 있다.

```text
중앙 예상값: 3.00%
예상 범위:   2.50% ~ 3.25%
```

이 범위 역시 통계적 방법과 과거 오차를 바탕으로 계산해야 하며 임의로 정하면
안 된다.

---

## 8. 시계열 데이터 검증

### 8.1 시계열이란?

시간 순서대로 관측된 데이터를 시계열 데이터라고 한다.

```text
2020년 금리
2021년 금리
2022년 금리
2023년 금리
2024년 금리
```

금리, 물가, 환율은 모두 시간 순서가 중요한 시계열 데이터다.

### 8.2 미래 데이터 누출

미래 데이터를 이용해 과거를 예측하면 모델이 정답을 미리 본 것과 비슷해진다.
이를 data leakage 또는 미래 정보 누출이라고 한다.

잘못된 예:

```text
2025년 데이터를 학습에 사용
        ↓
2020년 금리를 예측
```

실제 2020년 시점에는 2025년 데이터를 알 수 없었으므로 올바른 검증이 아니다.

### 8.3 올바른 시간순 분할

```text
2010~2022년: 학습 데이터
2023년:      검증 데이터
2024~2025년: 최종 테스트 데이터
```

- 학습 데이터: 모델이 패턴을 배우는 데이터
- 검증 데이터: 모델 설정을 선택하는 데이터
- 테스트 데이터: 마지막에 실제 성능을 평가하는 데이터

테스트 데이터를 보면서 계속 모델을 수정하면 테스트 데이터도 사실상 학습에
사용한 셈이 된다.

### 8.4 일반 무작위 분할의 문제

일반적인 `train_test_split`은 데이터를 섞을 수 있다.

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    shuffle=True,
)
```

시계열에서 `shuffle=True`를 사용하면 미래 관측값이 학습 데이터에 들어갈 수
있다. 따라서 시간순 분할 또는 `TimeSeriesSplit`을 고려해야 한다.

```python
from sklearn.model_selection import TimeSeriesSplit

splitter = TimeSeriesSplit(n_splits=5)
```

공식 참고:

- [scikit-learn 시계열 지연 특성과 검증 예제](https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html)

---

## 9. 데이터 수집 계획

### 9.1 한국 데이터

한국 금리와 경제지표는 한국은행 자료와 ECOS 경제통계시스템 등을 검토할 수
있다.

수집 후보:

- 한국은행 기준금리
- 소비자물가지수
- 원/달러 환율
- 국고채 금리
- 통화량
- 가계대출

### 9.2 미국 및 국제 데이터

미국 금리와 경제 데이터는 FRED API를 활용할 수 있다.

FRED API는 HTTPS 요청으로 경제 시계열 데이터를 JSON 또는 XML 형태로 제공한다.

공식 참고:

- [FRED API 개요](https://fred.stlouisfed.org/docs/api/fred/overview.html)
- [한국은행 통화정책 자료](https://www.bok.or.kr/portal/bbs/P0000559/list.do?menuNo=200690)

### 9.3 데이터 빈도 통일

경제지표마다 발표 주기가 다를 수 있다.

```text
기준금리: 회의 일정에 따라 변경
물가:     월별
GDP:      분기별
환율:     일별
```

모델 학습 전에는 월별 또는 분기별 등 하나의 기준으로 맞춰야 한다.

월별 데이터로 맞추는 예:

```text
일별 환율 → 월평균 환율
분기 GDP  → 해당 분기의 월에 연결
기준금리  → 각 월말 기준금리
```

어떤 방식으로 변환했는지 기록하지 않으면 모델 결과를 올바르게 해석하기 어렵다.

---

## 10. 최종 FastAPI 설계

### 10.1 요청 모델

```python
from pydantic import BaseModel, Field


class RatePredictionRequest(BaseModel):
    forecast_months: int = Field(default=3, ge=1, le=12)
```

요청 예:

```json
{
  "forecast_months": 3
}
```

### 10.2 응답 모델

```python
class RatePredictionResponse(BaseModel):
    current_rate: float
    predicted_rate: float
    direction: str
    lower_bound: float
    upper_bound: float
    model_name: str
```

응답 예:

```json
{
  "current_rate": 2.75,
  "predicted_rate": 3.0,
  "direction": "인상",
  "lower_bound": 2.5,
  "upper_bound": 3.25,
  "model_name": "baseline"
}
```

숫자는 API 형식을 설명하기 위한 예시다.

### 10.3 예측 엔드포인트

```python
@app.post(
    "/predict/rate",
    response_model=RatePredictionResponse,
    tags=["금리 예측"],
    summary="한국은행 기준금리 예측",
)
async def predict_rate(
    request: RatePredictionRequest,
) -> RatePredictionResponse:
    ...
```

Swagger에서는 다음 주소에서 요청과 응답 명세를 확인할 수 있다.

```text
http://127.0.0.1:8000/docs
```

---

## 11. 최종 프론트엔드 설계

프론트엔드에 다음 항목을 표시한다.

```text
현재 기준금리
예측 기간 선택
예상 기준금리
인상·동결·인하 방향
예측 하한과 상한
과거 금리와 예상 금리 차트
모델의 과거 평균 오차
마지막 데이터 업데이트 시점
```

프론트엔드 JavaScript 요청 예:

```javascript
const response = await fetch("/predict/rate", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    forecast_months: 3,
  }),
});

const prediction = await response.json();
```

사용자가 숫자를 확정된 사실로 오해하지 않도록 다음 문구도 표시한다.

```text
본 결과는 과거 데이터에 기반한 통계적 추정이며,
실제 금리 결정이나 투자 결과를 보장하지 않습니다.
```

---

## 12. 개발 단계별 목표

### 단계 1: 연습용 데이터

- 작은 CSV 파일 작성
- pandas로 파일 읽기
- 날짜순 정렬
- 입력값과 목표값 분리

### 단계 2: Baseline

- 현재 금리를 미래 금리로 예측
- MAE 계산
- 방향 정확도 계산

### 단계 3: 첫 머신러닝 모델

- Linear Regression 학습
- 시간순으로 학습·테스트 분리
- Baseline과 MAE 비교

### 단계 4: 추가 모델

- Random Forest 또는 Gradient Boosting 실험
- 입력 변수의 영향 확인
- 과적합 여부 확인

### 단계 5: 실제 데이터

- 한국은행·FRED 데이터 수집
- 데이터 발표 주기 통일
- 결측값 처리
- 데이터 출처와 업데이트 시점 기록

### 단계 6: FastAPI

- 모델 파일 저장·불러오기
- `/predict/rate` 구현
- 요청·응답 모델 정의
- 오류 처리
- Swagger 명세 작성

### 단계 7: 프론트엔드

- 예측 기간 입력
- API 호출
- 결과 카드
- 과거·예측 차트
- 오류와 로딩 화면

---

## 13. 주의사항

### 13.1 상관관계와 인과관계

어떤 경제지표가 금리와 함께 움직였다고 해서 그 지표가 금리 변화를 직접
발생시켰다고 단정할 수 없다.

### 13.2 데이터 개수

기준금리 결정 횟수는 주식의 일별 가격처럼 데이터가 매우 많지 않다. 입력 변수를
과도하게 늘리면 모델이 과거 데이터를 외우는 과적합이 발생하기 쉽다.

### 13.3 발표 시차

어떤 경제지표는 해당 월이 지난 뒤 발표된다. 예측 시점에 실제로 알 수 없었던
수정치나 확정치를 학습 입력에 넣으면 미래 정보 누출이 될 수 있다.

### 13.4 정책 결정의 특성

기준금리는 경제지표만으로 기계적으로 결정되지 않는다. 금융안정, 국제 정세,
정책 판단, 예상하지 못한 사건도 영향을 줄 수 있다.

### 13.5 결과 표현

피해야 하는 표현:

```text
3개월 후 금리는 반드시 3.00%가 됩니다.
```

더 적절한 표현:

```text
과거 데이터 기반 중앙 예상값은 3.00%이며,
과거 검증 오차를 고려한 예상 범위는 2.50~3.25%입니다.
```

---

## 14. 핵심 용어

| 용어 | 뜻 |
|---|---|
| Target | 모델이 예측할 정답 |
| Feature | 모델 판단에 사용하는 입력값 |
| Regression | 연속적인 숫자를 예측하는 문제 |
| Classification | 정해진 범주를 예측하는 문제 |
| Baseline | 복잡한 모델과 비교하는 단순 기준 |
| Training | 모델이 데이터에서 패턴을 학습하는 과정 |
| Validation | 모델 설정을 선택하고 점검하는 과정 |
| Test | 마지막에 일반화 성능을 평가하는 과정 |
| MAE | 예측값과 실제값의 절대 오차 평균 |
| Time series | 시간 순서대로 관측된 데이터 |
| Lag feature | 이전 시점의 값을 현재 입력으로 사용한 변수 |
| Data leakage | 예측 시점에 알 수 없는 정보가 학습에 들어가는 문제 |
| Overfitting | 모델이 과거 데이터만 지나치게 외우는 현상 |
| Uncertainty | 미래 결과가 하나로 확정되지 않는 불확실성 |

---

## 15. 첫 번째 실습 목표

다음 실습에서는 작은 연습용 금리 CSV를 만들고 baseline 모델을 구현한다.

완료 조건:

```text
1. CSV를 Python으로 읽을 수 있다.
2. 현재 금리를 3개월 후 금리로 예측한다.
3. 실제값과 예측값의 MAE를 계산한다.
4. 결과를 터미널에 출력한다.
5. Baseline의 의미를 설명할 수 있다.
```

첫 실습이 끝난 뒤에만 머신러닝 모델을 추가한다. 그래야 머신러닝이 실제로
얼마나 개선됐는지 비교할 수 있다.
