"""포스트 팬데믹 특성 공학과 시계열 교차검증으로 방향 모델을 튜닝한다.

실행:
    python -m ml.tune_post_pandemic_models
"""

import json
from collections import Counter
from itertools import product
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, recall_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from ml.baseline import get_direction, load_rows
from ml.classify_rate_direction import LABELS


PROJECT_DIR = Path(__file__).resolve().parent.parent
TRAIN_PATH = (
    PROJECT_DIR / "data" / "processed" / "monthly_interest_rate_data.csv"
)
FEATURE_PATH = (
    PROJECT_DIR / "data" / "processed" / "monthly_interest_rate_features.csv"
)
LIVE_PATH = PROJECT_DIR / "data" / "live" / "latest_features.json"
OUTPUT_PATH = PROJECT_DIR / "outputs" / "tuned_post_pandemic_forecast.json"
START_DATE = "2022-01"
N_SPLITS = 4
TEST_SIZE = 6
TARGET_GAP = 3

BASE_FEATURES = [
    "current_rate",
    "inflation",
    "exchange_rate",
    "unemployment",
    "bond_3y",
    "us_policy_rate",
]
ENGINEERED_FEATURES = [
    "inflation_change_1m",
    "inflation_change_3m",
    "inflation_change_6m",
    "exchange_rate_change_1m_pct",
    "exchange_rate_change_3m_pct",
    "exchange_rate_change_6m_pct",
    "bond_3y_change_1m",
    "bond_3y_change_3m",
    "bond_3y_change_6m",
    "korea_us_rate_spread",
    "bond_policy_spread",
    "rate_change_3m",
    "rate_direction_3m",
]
MODEL_FEATURES = BASE_FEATURES + ENGINEERED_FEATURES


def engineer_features(
    rows: list[dict[str, str | float]],
) -> list[dict[str, float | str]]:
    """월별 원자료에서 변화량·변화율·금리차 특성을 만든다."""
    result: list[dict[str, float | str]] = []
    for index in range(6, len(rows)):
        current = rows[index]
        record: dict[str, float | str] = {"date": str(current["date"])}
        for name in BASE_FEATURES:
            record[name] = float(current[name])

        for lag in (1, 3, 6):
            previous = rows[index - lag]
            record[f"inflation_change_{lag}m"] = (
                float(current["inflation"]) - float(previous["inflation"])
            )
            previous_exchange = float(previous["exchange_rate"])
            record[f"exchange_rate_change_{lag}m_pct"] = (
                float(current["exchange_rate"]) / previous_exchange - 1
            ) * 100
            record[f"bond_3y_change_{lag}m"] = (
                float(current["bond_3y"]) - float(previous["bond_3y"])
            )

        current_rate = float(current["current_rate"])
        rate_three_months_ago = float(rows[index - 3]["current_rate"])
        record["korea_us_rate_spread"] = (
            current_rate - float(current["us_policy_rate"])
        )
        record["bond_policy_spread"] = (
            float(current["bond_3y"]) - current_rate
        )
        record["rate_change_3m"] = current_rate - rate_three_months_ago
        record["rate_direction_3m"] = {
            "인하": -1.0,
            "동결": 0.0,
            "인상": 1.0,
        }[get_direction(rate_three_months_ago, current_rate)]
        result.append(record)
    return result


def to_matrix(rows: list[dict[str, float | str]]) -> np.ndarray:
    return np.array(
        [
            [float(row[name]) for name in MODEL_FEATURES]
            for row in rows
        ],
        dtype=float,
    )


def attach_targets(
    feature_rows: list[dict[str, float | str]],
    target_rows: list[dict[str, str]],
    start_date: str = START_DATE,
) -> tuple[list[dict[str, float | str]], np.ndarray]:
    targets = {
        row["date"]: get_direction(
            float(row["current_rate"]),
            float(row["rate_after_3_months"]),
        )
        for row in target_rows
    }
    matched_rows = [
        row for row in feature_rows
        if str(row["date"]) >= start_date and str(row["date"]) in targets
    ]
    labels = np.array(
        [targets[str(row["date"])] for row in matched_rows],
        dtype=object,
    )
    return matched_rows, labels


def make_forest(params: dict[str, object]) -> RandomForestClassifier:
    model_params = dict(params)
    class_weight = model_params.pop("class_weight")
    return RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        class_weight=class_weight,
        **model_params,
    )


def make_xgboost(params: dict[str, object], class_count: int) -> XGBClassifier:
    objective = "binary:logistic" if class_count == 2 else "multi:softprob"
    return XGBClassifier(
        objective=objective,
        n_estimators=200,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=2.0,
        random_state=42,
        n_jobs=-1,
        eval_metric="logloss" if class_count == 2 else "mlogloss",
        **params,
    )


def fit_predict_xgboost(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    params: dict[str, object],
) -> np.ndarray:
    """각 fold에 실제 존재하는 클래스만 연속 정수로 인코딩한다."""
    classes = sorted(set(str(value) for value in y_train))
    label_to_id = {label: index for index, label in enumerate(classes)}
    encoded = np.array([label_to_id[str(value)] for value in y_train])
    model_params = dict(params)
    use_balanced_weights = bool(
        model_params.pop("use_balanced_weights")
    )
    model = make_xgboost(model_params, len(classes))
    sample_weight = (
        compute_sample_weight("balanced", encoded)
        if use_balanced_weights
        else None
    )
    model.fit(
        x_train,
        encoded,
        sample_weight=sample_weight,
    )
    predicted_ids = model.predict(x_test)
    return np.array(
        [classes[int(value)] for value in predicted_ids],
        dtype=object,
    )


def score_predictions(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> dict[str, float]:
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
    }


def cross_validate(
    model_name: str,
    params: dict[str, object],
    x: np.ndarray,
    y: np.ndarray,
    splitter: TimeSeriesSplit,
) -> tuple[dict[str, float], list[dict[str, object]]]:
    all_actual: list[str] = []
    all_predicted: list[str] = []
    fold_details: list[dict[str, object]] = []

    for fold, (train_indices, test_indices) in enumerate(
        splitter.split(x),
        start=1,
    ):
        x_train, x_test = x[train_indices], x[test_indices]
        y_train, y_test = y[train_indices], y[test_indices]
        if model_name == "random_forest":
            model = make_forest(params)
            model.fit(x_train, y_train)
            predicted = model.predict(x_test)
        else:
            predicted = fit_predict_xgboost(
                x_train,
                y_train,
                x_test,
                params,
            )

        all_actual.extend(str(value) for value in y_test)
        all_predicted.extend(str(value) for value in predicted)
        fold_details.append(
            {
                "fold": fold,
                "train_samples": len(train_indices),
                "test_samples": len(test_indices),
                "metrics": score_predictions(y_test, predicted),
            }
        )

    metrics = score_predictions(
        np.array(all_actual, dtype=object),
        np.array(all_predicted, dtype=object),
    )
    return metrics, fold_details


def tune_model(
    model_name: str,
    candidates: list[dict[str, object]],
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[dict[str, object], dict[str, float], list[dict[str, object]]]:
    trials: list[tuple[dict[str, object], dict[str, float], list[dict[str, object]]]] = []
    for params in candidates:
        splitter = TimeSeriesSplit(
            n_splits=N_SPLITS,
            test_size=TEST_SIZE,
            gap=TARGET_GAP,
        )
        metrics, folds = cross_validate(
            model_name,
            params,
            x,
            y,
            splitter,
        )
        trials.append((params, metrics, folds))

    # 방향별 탐지와 전체 분류 성능을 함께 보는 Macro F1을 우선한다.
    return max(
        trials,
        key=lambda trial: (
            trial[1]["macro_f1"],
            trial[1]["accuracy"],
        ),
    )


def baseline_cross_validation(
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[dict[str, float], dict[str, int]]:
    splitter = TimeSeriesSplit(
        n_splits=N_SPLITS,
        test_size=TEST_SIZE,
        gap=TARGET_GAP,
    )
    test_indices = np.concatenate(
        [indices for _, indices in splitter.split(x)]
    )
    actual = y[test_indices]
    predicted = np.full(len(actual), "동결", dtype=object)
    return score_predictions(actual, predicted), dict(Counter(actual))


def final_probability(
    model_name: str,
    params: dict[str, object],
    x: np.ndarray,
    y: np.ndarray,
    x_live: np.ndarray,
) -> tuple[dict[str, float], list[float]]:
    if model_name == "random_forest":
        model = make_forest(params)
        model.fit(x, y)
        classes = [str(value) for value in model.classes_]
        raw = model.predict_proba(x_live)[0]
        importances = model.feature_importances_
    else:
        classes = sorted(set(str(value) for value in y))
        label_to_id = {label: index for index, label in enumerate(classes)}
        encoded = np.array([label_to_id[str(value)] for value in y])
        model_params = dict(params)
        use_balanced_weights = bool(
            model_params.pop("use_balanced_weights")
        )
        model = make_xgboost(model_params, len(classes))
        model.fit(
            x,
            encoded,
            sample_weight=(
                compute_sample_weight("balanced", encoded)
                if use_balanced_weights
                else None
            ),
        )
        raw = model.predict_proba(x_live)[0]
        importances = model.feature_importances_

    by_label = {
        label: float(probability)
        for label, probability in zip(classes, raw, strict=True)
    }
    return (
        {label: by_label.get(label, 0.0) for label in LABELS},
        [float(value) for value in importances],
    )


def main() -> None:
    monthly_rows = load_rows(FEATURE_PATH)
    target_rows = load_rows(TRAIN_PATH)
    engineered_rows = engineer_features(monthly_rows)
    train_rows, labels = attach_targets(engineered_rows, target_rows)
    x = to_matrix(train_rows)

    forest_candidates = [
        {
            "max_depth": depth,
            "min_samples_leaf": leaf,
            "max_features": max_features,
            "class_weight": class_weight,
        }
        for depth, leaf, max_features, class_weight in product(
            [2, 4, None],
            [2, 4],
            ["sqrt", 0.7],
            [None, "balanced"],
        )
    ]
    xgboost_candidates = [
        {
            "max_depth": depth,
            "learning_rate": learning_rate,
            "min_child_weight": child_weight,
            "use_balanced_weights": balanced_weights,
        }
        for depth, learning_rate, child_weight, balanced_weights in product(
            [1, 2, 3],
            [0.03, 0.08],
            [2, 5],
            [False, True],
        )
    ]

    forest_params, forest_metrics, forest_folds = tune_model(
        "random_forest",
        forest_candidates,
        x,
        labels,
    )
    xgboost_params, xgboost_metrics, xgboost_folds = tune_model(
        "xgboost",
        xgboost_candidates,
        x,
        labels,
    )
    baseline_metrics, validation_distribution = baseline_cross_validation(
        x,
        labels,
    )

    live_payload = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
    live_month = live_payload["as_of_date"][:7]
    combined_rows: list[dict[str, str | float]] = list(monthly_rows)
    live_row = {
        "date": live_month,
        **live_payload["features"],
    }
    if str(combined_rows[-1]["date"]) == live_month:
        combined_rows[-1] = live_row
    else:
        combined_rows.append(live_row)
    live_engineered = engineer_features(combined_rows)[-1]
    x_live = to_matrix([live_engineered])

    forest_probability, forest_importance = final_probability(
        "random_forest",
        forest_params,
        x,
        labels,
        x_live,
    )
    xgboost_probability, xgboost_importance = final_probability(
        "xgboost",
        xgboost_params,
        x,
        labels,
        x_live,
    )
    ensemble = {
        label: (
            forest_probability[label] + xgboost_probability[label]
        ) / 2
        for label in LABELS
    }

    def top_features(importances: list[float]) -> list[dict[str, float | str]]:
        ranked = sorted(
            zip(MODEL_FEATURES, importances, strict=True),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return [
            {"feature": name, "importance": round(value, 6)}
            for name, value in ranked[:8]
        ]

    result = {
        "analysis_period": {
            "start": train_rows[0]["date"],
            "training_end": train_rows[-1]["date"],
            "latest_input": live_payload["as_of_date"],
            "training_samples": len(train_rows),
        },
        "features": MODEL_FEATURES,
        "label_distribution": dict(Counter(labels)),
        "validation": {
            "method": "TimeSeriesSplit",
            "n_splits": N_SPLITS,
            "test_size_months": TEST_SIZE,
            "gap_months": TARGET_GAP,
            "selection_metric": "macro_f1",
            "test_label_distribution": validation_distribution,
            "hold_baseline_metrics": baseline_metrics,
        },
        "models": {
            "random_forest": {
                "best_params": forest_params,
                "cv_metrics": forest_metrics,
                "folds": forest_folds,
                "latest_probabilities": forest_probability,
                "top_features": top_features(forest_importance),
            },
            "xgboost": {
                "best_params": xgboost_params,
                "cv_metrics": xgboost_metrics,
                "folds": xgboost_folds,
                "latest_probabilities": xgboost_probability,
                "top_features": top_features(xgboost_importance),
            },
        },
        "latest_ensemble": {
            "direction": max(ensemble, key=ensemble.get),
            "probabilities": ensemble,
        },
        "warnings": [
            "튜닝과 성능 측정에 같은 교차검증 구간을 사용한 탐색 결과입니다.",
            "포스트 팬데믹 표본이 작아 확률과 중요도가 불안정할 수 있습니다.",
            "학습용 결과이며 금융·투자 판단에 사용하면 안 됩니다.",
        ],
    }
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("포스트 팬데믹 시차 특성 + TimeSeriesSplit 튜닝")
    print("-" * 78)
    print(
        f"학습: {train_rows[0]['date']} ~ {train_rows[-1]['date']} "
        f"({len(train_rows)}개), 특성 {len(MODEL_FEATURES)}개"
    )
    print(
        f"검증 정답 분포: {validation_distribution}\n"
        f"동결 Baseline: 정확도 {baseline_metrics['accuracy']:.2%}, "
        f"Macro F1 {baseline_metrics['macro_f1']:.3f}, "
        f"인하 탐지율 {baseline_metrics['cut_recall']:.2%}, "
        f"인상 탐지율 {baseline_metrics['hike_recall']:.2%}"
    )
    for name, params, metrics, probability in [
        (
            "Random Forest",
            forest_params,
            forest_metrics,
            forest_probability,
        ),
        ("XGBoost", xgboost_params, xgboost_metrics, xgboost_probability),
    ]:
        print(f"\n{name}")
        print(f"- 최적 설정: {params}")
        print(
            f"- CV 정확도 {metrics['accuracy']:.2%}, "
            f"Macro F1 {metrics['macro_f1']:.3f}"
        )
        print(
            f"- 인하 탐지율 {metrics['cut_recall']:.2%}, "
            f"동결 탐지율 {metrics['hold_recall']:.2%}, "
            f"인상 탐지율 {metrics['hike_recall']:.2%}"
        )
        print(
            f"- 최신 확률: 인하 {probability['인하']:.1%}, "
            f"동결 {probability['동결']:.1%}, "
            f"인상 {probability['인상']:.1%}"
        )
    print(
        f"\n두 모델 평균: {max(ensemble, key=ensemble.get)} "
        f"(인하 {ensemble['인하']:.1%}, 동결 {ensemble['동결']:.1%}, "
        f"인상 {ensemble['인상']:.1%})"
    )
    print(f"결과 저장 위치: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
