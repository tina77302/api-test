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
from sklearn.utils.class_weight import compute_sample_weight

from ml.baseline import get_direction, load_rows, predict_baseline
from ml.classify_rate_direction import (
    build_classifier,
    make_labels,
    probability_map,
)
from ml.compare_direction_models import (
    build_random_forest,
    build_xgboost,
    classifier_probability_map,
    labels_to_ids,
)
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

    direction_model = build_classifier()
    direction_model.fit(x_train, make_labels(train_rows))
    direction_probabilities = probability_map(direction_model, x_live)
    predicted_direction = max(
        direction_probabilities,
        key=direction_probabilities.get,
    )

    random_forest = build_random_forest()
    direction_labels = make_labels(train_rows)
    random_forest.fit(x_train, direction_labels)
    forest_probabilities = classifier_probability_map(
        random_forest,
        x_live,
    )

    xgboost = build_xgboost()
    encoded_direction_labels = labels_to_ids(direction_labels)
    xgboost.fit(
        x_train,
        encoded_direction_labels,
        sample_weight=compute_sample_weight(
            "balanced",
            encoded_direction_labels,
        ),
    )
    xgboost_probabilities = classifier_probability_map(
        xgboost,
        x_live,
        encoded_labels=True,
    )

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
            "direction_classifier": {
                "predicted_direction": predicted_direction,
                "probabilities": {
                    label: round(probability, 6)
                    for label, probability in direction_probabilities.items()
                },
            },
            "random_forest": {
                "predicted_direction": max(
                    forest_probabilities,
                    key=forest_probabilities.get,
                ),
                "probabilities": {
                    label: round(probability, 6)
                    for label, probability in forest_probabilities.items()
                },
            },
            "xgboost": {
                "predicted_direction": max(
                    xgboost_probabilities,
                    key=xgboost_probabilities.get,
                ),
                "probabilities": {
                    label: round(probability, 6)
                    for label, probability in xgboost_probabilities.items()
                },
            },
        },
        "features": features,
        "source_periods": live_payload["source_periods"],
        "warnings": [
            "현재 월이 끝나기 전의 잠정 입력을 사용했습니다.",
            "Linear Regression은 과거 테스트에서 Baseline보다 부정확했습니다.",
            "방향 분류 확률은 아직 확률 보정되지 않은 학습용 결과입니다.",
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
    print(
        "방향 분류 예측: "
        f"{predicted_direction} "
        f"(인하 {direction_probabilities['인하']:.1%}, "
        f"동결 {direction_probabilities['동결']:.1%}, "
        f"인상 {direction_probabilities['인상']:.1%})"
    )
    print(
        "Random Forest: "
        f"{max(forest_probabilities, key=forest_probabilities.get)} "
        f"(인하 {forest_probabilities['인하']:.1%}, "
        f"동결 {forest_probabilities['동결']:.1%}, "
        f"인상 {forest_probabilities['인상']:.1%})"
    )
    print(
        "XGBoost: "
        f"{max(xgboost_probabilities, key=xgboost_probabilities.get)} "
        f"(인하 {xgboost_probabilities['인하']:.1%}, "
        f"동결 {xgboost_probabilities['동결']:.1%}, "
        f"인상 {xgboost_probabilities['인상']:.1%})"
    )
    print("\n주의:")
    print("- 현재 월이 끝나기 전의 잠정 입력을 사용했습니다.")
    print("- Linear Regression은 과거 테스트에서 Baseline보다 부정확했습니다.")
    print("- 방향 분류 확률은 아직 확률 보정되지 않은 학습용 결과입니다.")
    print("- 학습 목적의 시험 결과이며 금융·투자 판단에 사용하면 안 됩니다.")
    print(f"\n결과 저장 위치: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
