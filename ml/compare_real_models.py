"""ECOS 실제 데이터에서 Baseline과 Linear Regression을 비교한다.

실행:
    python -m ml.compare_real_models
"""

from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.baseline import get_direction, load_rows, predict_baseline


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = (
    PROJECT_DIR / "data" / "processed" / "monthly_interest_rate_data.csv"
)
FEATURES = [
    "current_rate",
    "inflation",
    "exchange_rate",
    "unemployment",
    "bond_3y",
    "us_policy_rate",
]
TARGET = "rate_after_3_months"
TRAIN_RATIO = 0.80


def to_matrix(
    rows: list[dict[str, str]],
    columns: list[str],
) -> np.ndarray:
    return np.array(
        [[float(row[column]) for column in columns] for row in rows],
        dtype=float,
    )


def direction_accuracy(
    rows: list[dict[str, str]],
    predictions: np.ndarray,
) -> float:
    correct = 0
    for row, prediction in zip(rows, predictions, strict=True):
        current_rate = float(row["current_rate"])
        actual_rate = float(row[TARGET])
        if get_direction(current_rate, actual_rate) == get_direction(
            current_rate,
            float(prediction),
        ):
            correct += 1
    return correct / len(rows)


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(
            "실제 데이터가 없습니다. 먼저 다음을 실행하세요:\n"
            "python -m data_pipeline.collect_ecos_data"
        )

    rows = load_rows(DATA_PATH)
    split_index = int(len(rows) * TRAIN_RATIO)
    train_rows = rows[:split_index]
    test_rows = rows[split_index:]

    x_train = to_matrix(train_rows, FEATURES)
    y_train = to_matrix(train_rows, [TARGET]).ravel()
    x_test = to_matrix(test_rows, FEATURES)
    y_test = to_matrix(test_rows, [TARGET]).ravel()

    baseline_predictions = np.array(
        [
            predict_baseline(float(row["current_rate"]))
            for row in test_rows
        ],
        dtype=float,
    )

    linear_model = make_pipeline(StandardScaler(), LinearRegression())
    linear_model.fit(x_train, y_train)
    linear_predictions = linear_model.predict(x_test)

    baseline_mae = float(mean_absolute_error(y_test, baseline_predictions))
    linear_mae = float(mean_absolute_error(y_test, linear_predictions))
    baseline_direction = direction_accuracy(test_rows, baseline_predictions)
    linear_direction = direction_accuracy(test_rows, linear_predictions)

    print("ECOS 실제 데이터 시간순 분리")
    print("-" * 64)
    print(
        f"학습: {train_rows[0]['date']} ~ {train_rows[-1]['date']} "
        f"({len(train_rows)}개)"
    )
    print(
        f"테스트: {test_rows[0]['date']} ~ {test_rows[-1]['date']} "
        f"({len(test_rows)}개)"
    )

    print("\n모델 비교")
    print("-" * 64)
    print(f"{'모델':<22}{'MAE':>12}{'방향 정확도':>16}")
    print(
        f"{'Baseline':<22}"
        f"{baseline_mae:>10.4f}%p"
        f"{baseline_direction:>15.2%}"
    )
    print(
        f"{'Linear Regression':<22}"
        f"{linear_mae:>10.4f}%p"
        f"{linear_direction:>15.2%}"
    )

    print("\n해석")
    print("-" * 64)
    mae_difference = linear_mae - baseline_mae
    if mae_difference < 0:
        print(
            "Linear Regression의 MAE가 Baseline보다 "
            f"{abs(mae_difference):.4f}%p 작습니다."
        )
    else:
        print(
            "Linear Regression의 MAE가 Baseline보다 "
            f"{mae_difference:.4f}%p 큽니다."
        )
    print(
        "이 결과는 한 번의 시간 분할 결과입니다. 다음 단계에서는 "
        "TimeSeriesSplit으로 여러 기간을 반복 검증해야 합니다."
    )


if __name__ == "__main__":
    main()
