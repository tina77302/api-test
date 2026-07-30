"""데이터 설계를 개선한 계층형 3개월 금리 방향 모델.

실행:
    python -m ml.reliability_forecast
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, log_loss, recall_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.baseline import load_rows
from ml.classify_rate_direction import LABELS
from ml.tune_post_pandemic_models import (
    FEATURE_PATH,
    LIVE_PATH,
    MODEL_FEATURES,
    TRAIN_PATH,
    attach_targets,
    engineer_features,
    to_matrix,
)


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_DIR / "outputs" / "reliability_forecast.json"
START_DATE = "2008-01"
HALF_LIFE_MONTHS = 60
OUTER_SPLITS = 5
OUTER_TEST_MONTHS = 12
TARGET_GAP_MONTHS = 3
PARAMETERS = [
    {"C": c_value, "class_weight": class_weight}
    for c_value in (0.03, 0.1, 0.3, 1.0, 3.0)
    for class_weight in (None, "balanced")
]


def recency_weights(length: int) -> np.ndarray:
    """가장 최근 관측치의 가중치를 1로 두고 60개월마다 절반으로 낮춘다."""
    ages = np.arange(length - 1, -1, -1, dtype=float)
    return np.power(0.5, ages / HALF_LIFE_MONTHS)


def make_model(params: dict[str, object]) -> Pipeline:
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(
            C=float(params["C"]),
            class_weight=params["class_weight"],
            max_iter=2_000,
            random_state=42,
        ),
    )


def fit_model(
    x: np.ndarray,
    y: np.ndarray,
    params: dict[str, object],
) -> Pipeline:
    model = make_model(params)
    model.fit(
        x,
        y,
        logisticregression__sample_weight=recency_weights(len(y)),
    )
    return model


def tune_binary_model(
    x: np.ndarray,
    y: np.ndarray,
    gap: int,
) -> dict[str, object]:
    """안쪽 시계열 검증 Log Loss가 가장 낮은 설정을 선택한다."""
    if len(x) < 30:
        return {"C": 0.1, "class_weight": None}
    test_size = max(4, min(12, len(x) // 6))
    splitter = TimeSeriesSplit(n_splits=3, test_size=test_size, gap=gap)
    trials: list[tuple[float, dict[str, object]]] = []
    for params in PARAMETERS:
        losses: list[float] = []
        for train_indices, test_indices in splitter.split(x):
            y_train = y[train_indices]
            if len(set(y_train)) < 2:
                continue
            model = fit_model(x[train_indices], y_train, params)
            probabilities = model.predict_proba(x[test_indices])
            losses.append(
                float(
                    log_loss(
                        y[test_indices],
                        probabilities,
                        labels=list(model.classes_),
                    )
                )
            )
        if losses:
            trials.append((float(np.mean(losses)), params))
    if not trials:
        return {"C": 0.1, "class_weight": None}
    return min(trials, key=lambda trial: trial[0])[1]


def train_hierarchy(
    x: np.ndarray,
    directions: np.ndarray,
) -> tuple[Pipeline, Pipeline, dict[str, object], dict[str, object]]:
    change_labels = np.array(
        ["변경" if value != "동결" else "동결" for value in directions],
        dtype=object,
    )
    change_params = tune_binary_model(
        x,
        change_labels,
        TARGET_GAP_MONTHS,
    )
    change_model = fit_model(x, change_labels, change_params)

    changed_indices = np.flatnonzero(directions != "동결")
    changed_x = x[changed_indices]
    changed_labels = directions[changed_indices]
    direction_params = tune_binary_model(changed_x, changed_labels, 1)
    direction_model = fit_model(
        changed_x,
        changed_labels,
        direction_params,
    )
    return change_model, direction_model, change_params, direction_params


def class_probability(
    model: Pipeline,
    x: np.ndarray,
    label: str,
) -> np.ndarray:
    classes = list(model.classes_)
    if label not in classes:
        return np.zeros(len(x), dtype=float)
    return model.predict_proba(x)[:, classes.index(label)]


def hierarchical_probabilities(
    change_model: Pipeline,
    direction_model: Pipeline,
    x: np.ndarray,
) -> np.ndarray:
    change_probability = class_probability(change_model, x, "변경")
    cut_given_change = class_probability(direction_model, x, "인하")
    return np.column_stack(
        [
            change_probability * cut_given_change,
            1 - change_probability,
            change_probability * (1 - cut_given_change),
        ]
    )


def multiclass_brier(
    actual: np.ndarray,
    probabilities: np.ndarray,
) -> float:
    target = np.zeros_like(probabilities)
    label_to_index = {label: index for index, label in enumerate(LABELS)}
    for row_index, label in enumerate(actual):
        target[row_index, label_to_index[str(label)]] = 1
    return float(np.mean(np.sum((probabilities - target) ** 2, axis=1)))


def metrics(
    actual: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, float]:
    predicted = np.array(
        [LABELS[index] for index in np.argmax(probabilities, axis=1)],
        dtype=object,
    )
    recalls = recall_score(
        actual,
        predicted,
        labels=LABELS,
        average=None,
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_f1": float(
            f1_score(
                actual,
                predicted,
                labels=LABELS,
                average="macro",
                zero_division=0,
            )
        ),
        "cut_recall": float(recalls[0]),
        "hold_recall": float(recalls[1]),
        "hike_recall": float(recalls[2]),
        "brier_score": multiclass_brier(actual, probabilities),
    }


def main() -> None:
    monthly_rows = load_rows(FEATURE_PATH)
    target_rows = load_rows(TRAIN_PATH)
    engineered_rows = engineer_features(monthly_rows)
    all_rows, all_labels = attach_targets(
        engineered_rows,
        target_rows,
        start_date=START_DATE,
    )
    selected_indices = [
        index
        for index, row in enumerate(all_rows)
        if str(row["date"]) >= START_DATE
    ]
    rows = [all_rows[index] for index in selected_indices]
    labels = all_labels[selected_indices]
    x = to_matrix(rows)

    splitter = TimeSeriesSplit(
        n_splits=OUTER_SPLITS,
        test_size=OUTER_TEST_MONTHS,
        gap=TARGET_GAP_MONTHS,
    )
    actual_values: list[str] = []
    probability_values: list[list[float]] = []
    folds: list[dict[str, object]] = []
    for fold, (train_indices, test_indices) in enumerate(
        splitter.split(x),
        start=1,
    ):
        hierarchy = train_hierarchy(x[train_indices], labels[train_indices])
        probabilities = hierarchical_probabilities(
            hierarchy[0],
            hierarchy[1],
            x[test_indices],
        )
        fold_metrics = metrics(labels[test_indices], probabilities)
        actual_values.extend(str(value) for value in labels[test_indices])
        probability_values.extend(probabilities.tolist())
        folds.append(
            {
                "fold": fold,
                "train_period": [
                    rows[train_indices[0]]["date"],
                    rows[train_indices[-1]]["date"],
                ],
                "test_period": [
                    rows[test_indices[0]]["date"],
                    rows[test_indices[-1]]["date"],
                ],
                "test_distribution": dict(
                    Counter(labels[test_indices])
                ),
                "metrics": fold_metrics,
            }
        )

    actual = np.array(actual_values, dtype=object)
    probabilities = np.array(probability_values, dtype=float)
    model_metrics = metrics(actual, probabilities)
    baseline_probabilities = np.zeros_like(probabilities)
    baseline_probabilities[:, LABELS.index("동결")] = 1
    baseline_metrics = metrics(actual, baseline_probabilities)

    change_model, direction_model, change_params, direction_params = (
        train_hierarchy(x, labels)
    )
    live_payload = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
    live_month = live_payload["as_of_date"][:7]
    combined_rows: list[dict[str, str | float]] = list(monthly_rows)
    live_row = {"date": live_month, **live_payload["features"]}
    if str(combined_rows[-1]["date"]) == live_month:
        combined_rows[-1] = live_row
    else:
        combined_rows.append(live_row)
    live_features = engineer_features(combined_rows)[-1]
    live_probability = hierarchical_probabilities(
        change_model,
        direction_model,
        to_matrix([live_features]),
    )[0]
    latest = {
        label: float(live_probability[index])
        for index, label in enumerate(LABELS)
    }

    result = {
        "design": {
            "training_start": rows[0]["date"],
            "training_end": rows[-1]["date"],
            "training_samples": len(rows),
            "features": MODEL_FEATURES,
            "recency_weight_half_life_months": HALF_LIFE_MONTHS,
            "hierarchy": [
                "stage_1: change vs hold",
                "stage_2: cut vs hike conditional on change",
            ],
            "target_gap_months": TARGET_GAP_MONTHS,
        },
        "validation": {
            "method": "nested expanding TimeSeriesSplit",
            "outer_splits": OUTER_SPLITS,
            "outer_test_months": OUTER_TEST_MONTHS,
            "test_distribution": dict(Counter(actual)),
            "baseline_metrics": baseline_metrics,
            "model_metrics": model_metrics,
            "folds": folds,
        },
        "selected_params": {
            "change_vs_hold": change_params,
            "cut_vs_hike": direction_params,
        },
        "latest_prediction": {
            "as_of_date": live_payload["as_of_date"],
            "current_rate": live_payload["features"]["current_rate"],
            "direction": max(latest, key=latest.get),
            "probabilities": latest,
        },
        "reliability_assessment": {
            "beats_baseline_accuracy": (
                model_metrics["accuracy"] > baseline_metrics["accuracy"]
            ),
            "beats_baseline_brier": (
                model_metrics["brier_score"]
                < baseline_metrics["brier_score"]
            ),
            "status": (
                "improved"
                if (
                    model_metrics["accuracy"] > baseline_metrics["accuracy"]
                    and model_metrics["brier_score"]
                    < baseline_metrics["brier_score"]
                )
                else "experimental"
            ),
        },
        "warnings": [
            "월별 정책금리 자료이며 금통위 회의별 실시간 빈티지 데이터는 아닙니다.",
            "확률 보정은 충분한 추가 표본을 확보한 뒤 별도로 검증해야 합니다.",
            "학습용 결과이며 금융·투자 판단에 사용하면 안 됩니다.",
        ],
    }
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("신뢰도 개선 데이터 설계 모델")
    print("-" * 72)
    print(
        f"학습: {rows[0]['date']} ~ {rows[-1]['date']} "
        f"({len(rows)}개), 최근 가중치 반감기 {HALF_LIFE_MONTHS}개월"
    )
    print(f"외부 검증 정답: {dict(Counter(actual))}")
    for name, values in [
        ("동결 Baseline", baseline_metrics),
        ("계층형 Logistic", model_metrics),
    ]:
        print(
            f"{name:<18} 정확도 {values['accuracy']:.2%}, "
            f"Macro F1 {values['macro_f1']:.3f}, "
            f"Brier {values['brier_score']:.3f}"
        )
        print(
            f"{'':18} 인하 {values['cut_recall']:.2%}, "
            f"동결 {values['hold_recall']:.2%}, "
            f"인상 {values['hike_recall']:.2%}"
        )
    print(
        "\n최신 예측: "
        f"{max(latest, key=latest.get)} "
        f"(인하 {latest['인하']:.1%}, 동결 {latest['동결']:.1%}, "
        f"인상 {latest['인상']:.1%})"
    )
    print(f"결과 저장 위치: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
