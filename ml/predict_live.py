"""확정 월 데이터로 학습하고 최신 잠정 입력으로 시험 예측한다.

실행:
    python -m ml.predict_live
"""

import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.baseline import get_direction, load_rows, predict_baseline
from ml.compare_real_models import DATA_PATH, FEATURES, TARGET, to_matrix


PROJECT_DIR = Path(__file__).resolve().parent.parent
LIVE_PATH = PROJECT_DIR / "data" / "live" / "latest_features.json"
OUTPUT_PATH = PROJECT_DIR / "outputs" / "live_prediction.json"


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(
            "학습 데이터가 없습니다. 먼저 실제 데이터를 수집해주세요."
        )
    if not LIVE_PATH.exists():
        raise SystemExit(
            "최신 입력이 없습니다. 먼저 다음을 실행하세요:\n"
            "python -m data_pipeline.collect_live_features"
        )

    train_rows = load_rows(DATA_PATH)
    x_train = to_matrix(train_rows, FEATURES)
    y_train = to_matrix(train_rows, [TARGET]).ravel()

    live_payload = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
    features = live_payload["features"]
    x_live = np.array(
        [[float(features[name]) for name in FEATURES]],
        dtype=float,
    )

    linear_model = make_pipeline(StandardScaler(), LinearRegression())
    linear_model.fit(x_train, y_train)
    linear_prediction = float(linear_model.predict(x_live)[0])

    current_rate = float(features["current_rate"])
    baseline_prediction = predict_baseline(current_rate)

    result = {
        "as_of_date": live_payload["as_of_date"],
        "data_status": live_payload["status"],
        "target": "Korea policy rate three months ahead",
        "current_rate": round(current_rate, 4),
        "predictions": {
            "baseline": {
                "predicted_rate": round(baseline_prediction, 4),
                "direction": get_direction(
                    current_rate,
                    baseline_prediction,
                ),
            },
            "linear_regression": {
                "predicted_rate": round(linear_prediction, 4),
                "direction": get_direction(
                    current_rate,
                    linear_prediction,
                ),
            },
        },
        "features": features,
        "source_periods": live_payload["source_periods"],
        "warnings": [
            "현재 월이 끝나기 전의 잠정 입력을 사용했습니다.",
            "Linear Regression은 과거 테스트에서 Baseline보다 부정확했습니다.",
            "학습 목적의 시험 결과이며 금융·투자 판단에 사용하면 안 됩니다.",
        ],
    }
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("최신 잠정 데이터 기반 시험 예측")
    print("-" * 60)
    print(f"기준일: {live_payload['as_of_date']}")
    print(f"현재 한국 기준금리: {current_rate:.2f}%")
    print(
        f"Baseline 3개월 후 예측: {baseline_prediction:.3f}% "
        f"({get_direction(current_rate, baseline_prediction)})"
    )
    print(
        f"Linear Regression 3개월 후 예측: {linear_prediction:.3f}% "
        f"({get_direction(current_rate, linear_prediction)})"
    )
    print("\n주의:")
    print("- 현재 월이 끝나기 전의 잠정 입력을 사용했습니다.")
    print("- Linear Regression은 과거 테스트에서 Baseline보다 부정확했습니다.")
    print("- 학습 목적의 시험 결과이며 금융·투자 판단에 사용하면 안 됩니다.")
    print(f"\n결과 저장 위치: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
