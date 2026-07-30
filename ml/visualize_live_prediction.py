"""최신 실제 데이터와 3개월 후 시험 예측을 PNG로 시각화한다.

실행:
    python -m ml.visualize_live_prediction
"""

import json
import os
from datetime import date
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/api-test-matplotlib")

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_RATE_PATH = PROJECT_DIR / "data" / "raw" / "ecos_current_rate.json"
LIVE_PREDICTION_PATH = PROJECT_DIR / "outputs" / "live_prediction.json"
OUTPUT_PATH = PROJECT_DIR / "outputs" / "live_prediction_dashboard.png"


def add_months(value: date, months: int) -> date:
    zero_based = value.year * 12 + value.month - 1 + months
    year, month = divmod(zero_based, 12)
    return date(year, month + 1, 1)


def load_rate_history(start_year: int = 2024) -> tuple[list[date], list[float]]:
    rows = json.loads(RAW_RATE_PATH.read_text(encoding="utf-8"))
    values: dict[str, float] = {}
    for row in rows:
        time_value = str(row.get("TIME", ""))
        data_value = str(row.get("DATA_VALUE", "")).strip()
        if len(time_value) != 6 or int(time_value[:4]) < start_year:
            continue
        try:
            values[time_value] = float(data_value)
        except ValueError:
            continue

    sorted_months = sorted(values)
    dates = [
        date(int(month[:4]), int(month[4:]), 1)
        for month in sorted_months
    ]
    rates = [values[month] for month in sorted_months]
    return dates, rates


def main() -> None:
    if not RAW_RATE_PATH.exists() or not LIVE_PREDICTION_PATH.exists():
        raise SystemExit(
            "필요한 데이터가 없습니다. 다음 명령을 먼저 실행하세요:\n"
            "python -m data_pipeline.collect_ecos_data\n"
            "python -m data_pipeline.collect_live_features\n"
            "python -m ml.predict_live"
        )

    payload = json.loads(LIVE_PREDICTION_PATH.read_text(encoding="utf-8"))
    history_dates, history_rates = load_rate_history()

    as_of = date.fromisoformat(payload["as_of_date"])
    live_month = date(as_of.year, as_of.month, 1)
    target_month = add_months(live_month, 3)
    current_rate = float(payload["current_rate"])
    baseline = float(payload["predictions"]["baseline"]["predicted_rate"])
    linear = float(
        payload["predictions"]["linear_regression"]["predicted_rate"]
    )

    if not history_dates or history_dates[-1] < live_month:
        history_dates.append(live_month)
        history_rates.append(current_rate)

    figure = plt.figure(figsize=(14, 8.5))
    grid = figure.add_gridspec(
        2,
        2,
        width_ratios=[2.1, 1],
        height_ratios=[2, 1],
        hspace=0.35,
        wspace=0.23,
    )
    rate_axis = figure.add_subplot(grid[:, 0])
    prediction_axis = figure.add_subplot(grid[0, 1])
    probability_axis = figure.add_subplot(grid[1, 1])

    figure.suptitle(
        "Korea Policy Rate: Latest Data and 3-Month Practice Forecast",
        fontsize=17,
        fontweight="bold",
    )

    rate_axis.step(
        history_dates,
        history_rates,
        where="post",
        linewidth=3,
        color="#17211c",
        label="Observed policy rate",
    )
    rate_axis.scatter(
        [live_month],
        [current_rate],
        s=100,
        color="#17211c",
        zorder=4,
    )
    rate_axis.plot(
        [live_month, target_month],
        [current_rate, baseline],
        linestyle="--",
        linewidth=2.5,
        color="#ee6b3b",
        label=f"Baseline: {baseline:.3f}%",
    )
    rate_axis.plot(
        [live_month, target_month],
        [current_rate, linear],
        linestyle="-.",
        linewidth=2.5,
        color="#245c46",
        label=f"Linear Regression: {linear:.3f}%",
    )
    rate_axis.scatter(
        [target_month, target_month],
        [baseline, linear],
        s=110,
        color=["#ee6b3b", "#245c46"],
        zorder=4,
    )
    rate_axis.axvline(
        live_month,
        color="#777777",
        linestyle=":",
        alpha=0.8,
    )
    rate_axis.text(
        live_month,
        rate_axis.get_ylim()[1],
        f"  As of {payload['as_of_date']}",
        va="top",
        color="#555555",
    )
    rate_axis.set_title("Observed history and forecast points")
    rate_axis.set_ylabel("Policy rate (%)")
    rate_axis.set_xlabel("Month")
    rate_axis.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    rate_axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    rate_axis.tick_params(axis="x", rotation=45)
    rate_axis.grid(alpha=0.25)
    rate_axis.legend(loc="best")

    names = ["Current", "Baseline", "Linear"]
    values = [current_rate, baseline, linear]
    colors = ["#17211c", "#ee6b3b", "#245c46"]
    bars = prediction_axis.bar(names, values, color=colors)
    prediction_axis.bar_label(bars, fmt="%.3f%%", padding=4)
    prediction_axis.set_ylim(
        max(0, min(values) - 0.35),
        max(values) + 0.35,
    )
    prediction_axis.set_ylabel("Rate (%)")
    prediction_axis.set_title(
        f"Target month: {target_month:%Y-%m}"
    )
    prediction_axis.grid(axis="y", alpha=0.2)

    direction_result = payload["predictions"]["direction_classifier"]
    probability_by_label = direction_result["probabilities"]
    direction_labels = ["Cut", "Hold", "Hike"]
    probability_values = [
        probability_by_label["인하"] * 100,
        probability_by_label["동결"] * 100,
        probability_by_label["인상"] * 100,
    ]
    probability_bars = probability_axis.barh(
        direction_labels,
        probability_values,
        color=["#377eb8", "#777777", "#e34a33"],
    )
    probability_axis.bar_label(
        probability_bars,
        fmt="%.1f%%",
        padding=4,
    )
    probability_axis.set_xlim(0, max(100, max(probability_values) + 12))
    probability_axis.set_xlabel("Uncalibrated model probability (%)")
    predicted_direction_english = {
        "인하": "Cut",
        "동결": "Hold",
        "인상": "Hike",
    }[direction_result["predicted_direction"]]
    probability_axis.set_title(
        "Direction classifier: "
        f"{predicted_direction_english}"
    )
    probability_axis.grid(axis="x", alpha=0.2)

    figure.text(
        0.5,
        0.015,
        (
            "Partial current-month inputs. Uncalibrated probabilities. "
            "Practice model only; "
            "not financial or investment advice. "
            "Linear Regression underperformed the baseline in backtesting."
        ),
        ha="center",
        color="#8b2f20",
        fontsize=9.5,
    )
    figure.subplots_adjust(top=0.91, bottom=0.10)

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    figure.savefig(OUTPUT_PATH, dpi=160, bbox_inches="tight")
    plt.close(figure)
    print(f"시각화 저장 위치: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
