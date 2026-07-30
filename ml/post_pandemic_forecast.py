"""2022년 이후 데이터만 사용해 3개월 뒤 금리 방향을 예측한다.

실행:
    python -m ml.post_pandemic_forecast
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, recall_score
from sklearn.utils.class_weight import compute_sample_weight

from ml.baseline import load_rows
from ml.classify_rate_direction import LABELS, build_classifier, make_labels
from ml.compare_direction_models import (
    build_random_forest,
    build_xgboost,
    classifier_probability_map,
    ids_to_labels,
    labels_to_ids,
)
from ml.compare_real_models import DATA_PATH, FEATURES, to_matrix


PROJECT_DIR = Path(__file__).resolve().parent.parent
LIVE_PATH = PROJECT_DIR / "data" / "live" / "latest_features.json"
OUTPUT_PATH = PROJECT_DIR / "outputs" / "post_pandemic_forecast.json"
START_DATE = "2022-01"
MINIMUM_TRAIN_ROWS = 24
TARGET_GAP_MONTHS = 3


def fit_models(
    rows: list[dict[str, str]],
) -> tuple[object, object, object]:
    x_train = to_matrix(rows, FEATURES)
    labels = make_labels(rows)

    logistic = build_classifier()
    logistic.fit(x_train, labels)

    forest = build_random_forest()
    forest.fit(x_train, labels)

    xgboost = build_xgboost()
    encoded = labels_to_ids(labels)
    xgboost.fit(
        x_train,
        encoded,
        sample_weight=compute_sample_weight("balanced", encoded),
    )
    return logistic, forest, xgboost


def walk_forward_validate(
    rows: list[dict[str, str]],
) -> tuple[dict[str, dict[str, float | int]], dict[str, int]]:
    actual: list[str] = []
    predictions = {
        "hold_baseline": [],
        "logistic_regression": [],
        "random_forest": [],
        "xgboost": [],
    }

    first_test_index = MINIMUM_TRAIN_ROWS + TARGET_GAP_MONTHS
    for test_index in range(first_test_index, len(rows)):
        # test 시점에는 3개월 후 정답이 이미 공개된 행만 학습에 사용한다.
        train_rows = rows[: test_index - TARGET_GAP_MONTHS]
        if set(make_labels(train_rows)) != set(LABELS):
            # XGBoost 다중 분류는 학습 구간에 세 클래스가 모두 필요하다.
            continue
        test_row = rows[test_index]
        models = fit_models(train_rows)
        x_test = to_matrix([test_row], FEATURES)

        actual.append(str(make_labels([test_row])[0]))
        predictions["hold_baseline"].append("동결")
        predictions["logistic_regression"].append(
            str(models[0].predict(x_test)[0])
        )
        predictions["random_forest"].append(
            str(models[1].predict(x_test)[0])
        )
        predictions["xgboost"].append(
            str(ids_to_labels(models[2].predict(x_test))[0])
        )

    actual_array = np.array(actual, dtype=object)
    result: dict[str, dict[str, float | int]] = {}
    for name, values in predictions.items():
        predicted = np.array(values, dtype=object)
        result[name] = {
            "samples": len(actual),
            "accuracy": round(
                float(accuracy_score(actual_array, predicted)),
                6,
            ),
            "balanced_accuracy": round(
                float(
                    recall_score(
                        actual_array,
                        predicted,
                        labels=LABELS,
                        average="macro",
                        zero_division=0,
                    )
                ),
                6,
            ),
            "macro_f1": round(
                float(
                    f1_score(
                        actual_array,
                        predicted,
                        labels=LABELS,
                        average="macro",
                        zero_division=0,
                    )
                ),
                6,
            ),
        }
    return result, dict(Counter(actual))


def main() -> None:
    rows = [
        row for row in load_rows(DATA_PATH)
        if row["date"] >= START_DATE
    ]
    if len(rows) < MINIMUM_TRAIN_ROWS + TARGET_GAP_MONTHS + 1:
        raise SystemExit("포스트 팬데믹 학습 데이터가 부족합니다.")

    live_payload = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
    live_features = live_payload["features"]
    x_live = np.array(
        [[float(live_features[name]) for name in FEATURES]],
        dtype=float,
    )

    validation, validation_distribution = walk_forward_validate(rows)
    logistic, forest, xgboost = fit_models(rows)
    probabilities = {
        "logistic_regression": classifier_probability_map(
            logistic,
            x_live,
        ),
        "random_forest": classifier_probability_map(
            forest,
            x_live,
        ),
        "xgboost": classifier_probability_map(
            xgboost,
            x_live,
            encoded_labels=True,
        ),
    }
    ensemble = {
        label: float(
            np.mean(
                [model_probabilities[label] for model_probabilities in probabilities.values()]
            )
        )
        for label in LABELS
    }

    result = {
        "analysis_period": {
            "definition": "post-pandemic",
            "start": rows[0]["date"],
            "training_end": rows[-1]["date"],
            "latest_input": live_payload["as_of_date"],
            "training_samples": len(rows),
        },
        "target": "Korea policy-rate direction three months ahead",
        "label_distribution": dict(Counter(make_labels(rows))),
        "validation": {
            "method": (
                "expanding-window walk-forward with a three-month target gap"
            ),
            "test_label_distribution": validation_distribution,
            "results": validation,
        },
        "latest_prediction": {
            "current_rate": float(live_features["current_rate"]),
            "models": {
                name: {
                    "direction": max(values, key=values.get),
                    "probabilities": {
                        label: round(value, 6)
                        for label, value in values.items()
                    },
                }
                for name, values in probabilities.items()
            },
            "equal_weight_ml_ensemble": {
                "direction": max(ensemble, key=ensemble.get),
                "probabilities": {
                    label: round(value, 6)
                    for label, value in ensemble.items()
                },
            },
        },
        "warnings": [
            "2022년 이후 표본만 사용해 학습 데이터가 매우 적습니다.",
            "확률 보정을 거치지 않은 학습용 모델 출력입니다.",
            "금융 또는 투자 판단에 사용하면 안 됩니다.",
        ],
    }
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("포스트 팬데믹(2022년 이후) 3개월 금리 방향 분석")
    print("-" * 72)
    print(
        f"학습 기간: {rows[0]['date']} ~ {rows[-1]['date']} "
        f"({len(rows)}개)"
    )
    print(f"정답 분포: {dict(Counter(make_labels(rows)))}")
    print("\n순차 검증")
    for name, metrics in validation.items():
        print(
            f"- {name:<22} 정확도 {metrics['accuracy']:.2%}, "
            f"균형 정확도 {metrics['balanced_accuracy']:.2%}, "
            f"Macro F1 {metrics['macro_f1']:.3f}"
        )
    print("\n최신 3개월 방향 예측")
    for name, values in probabilities.items():
        print(
            f"- {name:<22} {max(values, key=values.get)}: "
            f"인하 {values['인하']:.1%}, 동결 {values['동결']:.1%}, "
            f"인상 {values['인상']:.1%}"
        )
    print(
        f"- {'ML 평균':<22} {max(ensemble, key=ensemble.get)}: "
        f"인하 {ensemble['인하']:.1%}, 동결 {ensemble['동결']:.1%}, "
        f"인상 {ensemble['인상']:.1%}"
    )
    print(f"\n결과 저장 위치: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
