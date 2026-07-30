"""모델 비교 결과를 PNG 그래프로 저장한다.

실행:
    python -m ml.visualize_comparison
"""

import os
from pathlib import Path

# Matplotlib이 읽기 전용 홈 폴더 대신 쓸 수 있는 임시 cache를 사용한다.
os.environ.setdefault("MPLCONFIGDIR", "/tmp/api-test-matplotlib")

import matplotlib
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.baseline import DATA_PATH, load_rows, predict_baseline
from ml.compare_models import (
    TRAIN_RATIO,
    calculate_direction_accuracy,
    to_feature_matrix,
    to_target_array,
)


# 화면이 없는 WSL 환경에서도 이미지 파일을 만들 수 있는 backend다.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
OUTPUT_PATH = OUTPUT_DIR / "model_comparison.png"


def main() -> None:
    rows = load_rows(DATA_PATH)
    split_index = int(len(rows) * TRAIN_RATIO)
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

    linear_model = make_pipeline(StandardScaler(), LinearRegression())
    linear_model.fit(x_train, y_train)
    linear_predictions = linear_model.predict(x_test)

    baseline_mae = float(mean_absolute_error(y_test, baseline_predictions))
    linear_mae = float(mean_absolute_error(y_test, linear_predictions))
    baseline_direction = calculate_direction_accuracy(
        test_rows,
        baseline_predictions,
    )
    linear_direction = calculate_direction_accuracy(
        test_rows,
        linear_predictions,
    )

    dates = [row["date"] for row in test_rows]
    x_positions = np.arange(len(dates))

    figure, (rate_axis, score_axis) = plt.subplots(
        2,
        1,
        figsize=(11, 9),
        gridspec_kw={"height_ratios": [2, 1]},
    )
    figure.suptitle(
        "Interest Rate Model Comparison (Synthetic Practice Data)",
        fontsize=16,
        fontweight="bold",
    )

    rate_axis.plot(
        x_positions,
        y_test,
        marker="o",
        linewidth=3,
        color="#17211c",
        label="Actual rate",
    )
    rate_axis.plot(
        x_positions,
        baseline_predictions,
        marker="s",
        linestyle="--",
        linewidth=2,
        color="#ee6b3b",
        label="Baseline",
    )
    rate_axis.plot(
        x_positions,
        linear_predictions,
        marker="^",
        linestyle="-.",
        linewidth=2,
        color="#245c46",
        label="Linear Regression",
    )
    rate_axis.set_title("Actual vs. predicted rate in the test period")
    rate_axis.set_ylabel("Policy rate (%)")
    rate_axis.set_xticks(x_positions, dates)
    rate_axis.grid(alpha=0.25)
    rate_axis.legend()

    model_names = ["Baseline", "Linear Regression"]
    mae_values = [baseline_mae, linear_mae]
    direction_values = [baseline_direction * 100, linear_direction * 100]

    width = 0.35
    bar_positions = np.arange(len(model_names))
    mae_bars = score_axis.bar(
        bar_positions - width / 2,
        mae_values,
        width,
        color="#ee6b3b",
        label="MAE (%p, lower is better)",
    )
    score_axis.set_ylabel("MAE (%p)")
    score_axis.set_xticks(bar_positions, model_names)
    score_axis.grid(axis="y", alpha=0.25)

    direction_axis = score_axis.twinx()
    direction_bars = direction_axis.bar(
        bar_positions + width / 2,
        direction_values,
        width,
        color="#245c46",
        label="Direction accuracy (%, higher is better)",
    )
    direction_axis.set_ylabel("Direction accuracy (%)")
    direction_axis.set_ylim(0, 100)

    score_axis.bar_label(mae_bars, fmt="%.4f")
    direction_axis.bar_label(direction_bars, fmt="%.1f%%")

    handles_1, labels_1 = score_axis.get_legend_handles_labels()
    handles_2, labels_2 = direction_axis.get_legend_handles_labels()
    score_axis.legend(handles_1 + handles_2, labels_1 + labels_2, loc="upper left")

    figure.text(
        0.5,
        0.01,
        "Practice only: this chart is not a real-world interest-rate forecast.",
        ha="center",
        color="#7a3020",
    )
    figure.tight_layout(rect=(0, 0.04, 1, 0.96))

    OUTPUT_DIR.mkdir(exist_ok=True)
    figure.savefig(OUTPUT_PATH, dpi=160, bbox_inches="tight")
    plt.close(figure)

    print(f"그래프를 저장했습니다: {OUTPUT_PATH}")
    print(f"Baseline MAE: {baseline_mae:.4f}%p")
    print(f"Linear Regression MAE: {linear_mae:.4f}%p")


if __name__ == "__main__":
    main()
