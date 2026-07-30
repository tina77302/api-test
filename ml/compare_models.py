
"""Baseline과 Linear Regression을 같은 테스트 기간에서 비교한다.

실행:
    python -m ml.compare_models
"""

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.baseline import DATA_PATH, get_direction, load_rows, predict_baseline


FEATURES = [
    "current_rate",
    "inflation",
    "exchange_rate",
    "unemployment",
    "gdp_growth",
    "bond_3y",
    "us_policy_rate",
]
TARGET = "rate_after_3_months"
TRAIN_RATIO = 0.75


@dataclass
class Evaluation:
    name: str
    mae: float
    direction_accuracy: float


def to_feature_matrix(rows: list[dict[str, str]]) -> np.ndarray:
    """CSV 행을 모델 입력용 2차원 숫자 배열로 변환한다."""
    return np.array(
        [[float(row[feature]) for feature in FEATURES] for row in rows],
        dtype=float,
    )


def to_target_array(rows: list[dict[str, str]]) -> np.ndarray:
    """CSV 행에서 목표값을 1차원 숫자 배열로 변환한다."""
    return np.array([float(row[TARGET]) for row in rows], dtype=float)


def calculate_direction_accuracy(
    rows: list[dict[str, str]],
    predictions: np.ndarray,
) -> float:
    """실제 방향과 예측 방향이 일치한 비율을 계산한다."""
    correct = 0
    for row, prediction in zip(rows, predictions, strict=True):
        current_rate = float(row["current_rate"])
        actual_rate = float(row[TARGET])
        actual_direction = get_direction(current_rate, actual_rate)
        predicted_direction = get_direction(current_rate, float(prediction))
        if actual_direction == predicted_direction:
            correct += 1
    return correct / len(rows)


def evaluate_model(
    name: str,
    test_rows: list[dict[str, str]],
    actual: np.ndarray,
    predictions: np.ndarray,
) -> Evaluation:
    """동일한 실제값을 기준으로 MAE와 방향 정확도를 계산한다."""
    return Evaluation(
        name=name,
        mae=float(mean_absolute_error(actual, predictions)),
        direction_accuracy=calculate_direction_accuracy(test_rows, predictions),
    )


def main() -> None:
    rows = load_rows(DATA_PATH)
    split_index = int(len(rows) * TRAIN_RATIO)

    # 데이터를 섞지 않고 과거와 미래 순서로 나눈다.
    train_rows = rows[:split_index]
    test_rows = rows[split_index:]

    x_train = to_feature_matrix(train_rows)
    y_train = to_target_array(train_rows)
    x_test = to_feature_matrix(test_rows)
    y_test = to_target_array(test_rows)

    baseline_predictions = np.array(
        [
            predict_baseline(float(row["current_rate"]))
            for row in test_rows
        ],
        dtype=float,
    )

    # StandardScaler는 입력 변수들의 단위 차이를 줄인다.
    linear_model = make_pipeline(
        StandardScaler(),
        LinearRegression(),
    )
    linear_model.fit(x_train, y_train)
    linear_predictions = linear_model.predict(x_test)

    baseline_result = evaluate_model(
        "Baseline",
        test_rows,
        y_test,
        baseline_predictions,
    )
    linear_result = evaluate_model(
        "Linear Regression",
        test_rows,
        y_test,
        linear_predictions,
    )

    print("시간순 데이터 분리")
    print("-" * 60)
    print(
        f"학습: {train_rows[0]['date']} ~ {train_rows[-1]['date']} "
        f"({len(train_rows)}개)"
    )
    print(
        f"테스트: {test_rows[0]['date']} ~ {test_rows[-1]['date']} "
        f"({len(test_rows)}개)"
    )

    print("\n테스트 기간 예측")
    print("-" * 60)
    print("날짜       실제금리  Baseline  Linear Regression")
    for row, actual, baseline, linear in zip(
        test_rows,
        y_test,
        baseline_predictions,
        linear_predictions,
        strict=True,
    ):
        print(
            f"{row['date']}    "
            f"{actual:>5.2f}%     "
            f"{baseline:>5.2f}%         "
            f"{linear:>7.3f}%"
        )

    print("\n모델 비교")
    print("-" * 60)
    print(f"{'모델':<22}{'MAE':>12}{'방향 정확도':>16}")
    for result in [baseline_result, linear_result]:
        print(
            f"{result.name:<22}"
            f"{result.mae:>10.4f}%p"
            f"{result.direction_accuracy:>15.2%}"
        )

    print("\n판정")
    print("-" * 60)
    if linear_result.mae < baseline_result.mae:
        improvement = baseline_result.mae - linear_result.mae
        print(
            "Linear Regression의 MAE가 Baseline보다 "
            f"{improvement:.4f}%p 작습니다."
        )
    elif linear_result.mae > baseline_result.mae:
        degradation = linear_result.mae - baseline_result.mae
        print(
            "Linear Regression의 MAE가 Baseline보다 "
            f"{degradation:.4f}%p 큽니다."
        )
        print("복잡한 모델이 항상 더 좋은 것은 아닙니다.")
    else:
        print("두 모델의 MAE가 같습니다.")

    print(
        "\n주의: 데이터가 24개뿐인 가상 실습이므로 "
        "실제 금리 예측 성능으로 해석하면 안 됩니다."
    )


if __name__ == "__main__":
    main()
