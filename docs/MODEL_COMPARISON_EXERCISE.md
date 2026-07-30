# 두 번째 실습: Baseline과 Linear Regression 비교

## 비교 원칙

두 모델을 공정하게 비교하려면 다음 조건이 같아야 한다.

```text
같은 테스트 기간
같은 실제 정답
같은 평가 지표
```

이번 실습에서는 24개월 데이터를 섞지 않고 시간순으로 나눈다.

```text
앞 75%: 학습 데이터
뒤 25%: 테스트 데이터
```

Baseline은 학습이 필요 없지만 Linear Regression은 앞 75% 데이터로 학습한다.
두 모델 모두 뒤 25%에서 평가한다.

## 실행

```bash
source .venv/bin/activate
python -m ml.compare_models
```

## 그래프로 보기

```bash
python -m ml.visualize_comparison
```

실행 후 다음 이미지 파일이 생성된다.

```text
outputs/model_comparison.png
```

VS Code 파일 탐색기에서 이 PNG 파일을 선택하면 실제 금리와 두 모델의 예측값,
MAE, 방향 정확도를 그래프로 확인할 수 있다.

## 사용하는 입력값

```python
FEATURES = [
    "current_rate",
    "inflation",
    "exchange_rate",
    "unemployment",
    "gdp_growth",
    "bond_3y",
    "us_policy_rate",
]
```

목표값:

```python
TARGET = "rate_after_3_months"
```

## 모델 1: Baseline

```text
예측값 = 현재 금리
```

금리 동결이 계속된다고 가정한다.

## 모델 2: Linear Regression

여러 경제지표와 3개월 후 금리 사이의 선형 관계를 학습한다.

```python
linear_model.fit(x_train, y_train)
linear_predictions = linear_model.predict(x_test)
```

`StandardScaler`는 환율처럼 값이 큰 변수와 금리처럼 값이 작은 변수의 단위
차이를 줄인다.

## 평가 지표

### MAE

```text
실제 금리와 예측 금리 차이의 절대값 평균
```

작을수록 좋다.

### 방향 정확도

```text
인상·동결·인하 방향을 맞힌 비율
```

클수록 좋다.

## 결과 해석

예를 들어:

```text
Baseline MAE:          0.30%p
Linear Regression MAE: 0.20%p
```

같은 테스트 기간에서 Linear Regression이 평균적으로 `0.10%p` 더 정확했다는
뜻이다.

반대로 Linear Regression의 MAE가 더 크면 복잡한 모델이 baseline보다 나쁜
것이다. 데이터가 적거나, 과적합됐거나, 입력 변수와 목표값의 관계가 단순 선형이
아닐 수 있다.

## 반드시 기억할 점

현재 데이터는 24개뿐인 가상 연습 데이터다. 이 결과로 실제 한국은행 기준금리를
예측하거나 투자 판단을 하면 안 된다.

실제 프로젝트에서는:

1. 공식 데이터를 더 길게 수집한다.
2. 발표 당시 알 수 있었던 값만 사용한다.
3. 여러 시간 구간으로 반복 검증한다.
4. baseline을 항상 함께 평가한다.
5. 예상 범위와 과거 오차를 표시한다.
