# 첫 번째 실습: 연습용 금리 데이터와 Baseline

## 실습 목표

이번 실습에서는 다음 흐름을 직접 확인한다.

```text
CSV 데이터 읽기
    ↓
현재 금리 확인
    ↓
3개월 후 금리를 현재 금리로 예측
    ↓
실제 금리와 비교
    ↓
MAE와 방향 정확도 계산
```

## 파일

```text
data/sample_interest_rates.csv  연습용 데이터
ml/baseline.py                  baseline 평가 코드
```

`sample_interest_rates.csv`는 학습 구조를 이해하기 위한 연습용 데이터다. 일부
경제 흐름을 참고해 구성했지만 공식 통계 분석에 그대로 사용하면 안 된다.

## 데이터 열

| 열 | 의미 |
|---|---|
| `date` | 관측 월 |
| `current_rate` | 해당 월의 현재 기준금리 |
| `inflation` | 물가 상승률 입력값 |
| `exchange_rate` | 원/달러 환율 입력값 |
| `unemployment` | 실업률 입력값 |
| `gdp_growth` | 경제성장률 입력값 |
| `bond_3y` | 국고채 3년 금리 입력값 |
| `us_policy_rate` | 미국 정책금리 입력값 |
| `rate_after_3_months` | 모델이 맞힐 3개월 후 금리 |

현재 baseline은 여러 경제 입력값 중 `current_rate`만 사용한다. 나머지 입력값은
다음 머신러닝 실습에서 사용한다.

## 실행

프로젝트 폴더의 WSL 터미널에서:

```bash
source .venv/bin/activate
python ml/baseline.py
```

## Baseline 규칙

```python
def predict_baseline(current_rate: float) -> float:
    return current_rate
```

이 함수는 금리가 앞으로도 현재 수준을 유지한다고 가정한다.

```text
현재 금리 3.50% → 3개월 후 예측 3.50%
현재 금리 3.25% → 3개월 후 예측 3.25%
```

## MAE 계산

각 행의 절대 오차:

```text
절대 오차 = |실제 3개월 후 금리 - 예측 금리|
```

전체 MAE:

```text
MAE = 모든 절대 오차의 합 ÷ 데이터 개수
```

MAE가 작을수록 실제 금리와 예측 금리의 평균적인 차이가 작다.

## 직접 확인할 내용

1. 금리가 동결된 기간에는 baseline이 왜 잘 맞는가?
2. 금리가 인하되기 시작하면 baseline은 왜 틀리는가?
3. MAE의 단위가 왜 `%`가 아니라 `%p`인가?
4. baseline이 항상 `동결`을 예측하는 이유는 무엇인가?
5. 머신러닝 모델은 이 baseline보다 어떤 지표에서 좋아야 하는가?

## 다음 실습

다음에는 같은 CSV를 사용해:

1. 데이터를 시간순으로 학습·테스트 분리한다.
2. 여러 경제지표를 입력값으로 선택한다.
3. 첫 Linear Regression 모델을 학습한다.
4. baseline과 머신러닝의 MAE를 비교한다.
