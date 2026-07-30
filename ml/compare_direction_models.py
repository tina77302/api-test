"""금리 방향 분류 모델 네 가지를 같은 시간 구간에서 비교한다.

실행:
    python -m ml.compare_direction_models
"""

from collections import Counter

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    log_loss,
)
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from ml.baseline import load_rows
from ml.classify_rate_direction import (
    LABELS,
    TRAIN_RATIO,
    build_classifier,
    make_labels,
)
from ml.compare_real_models import DATA_PATH, FEATURES, to_matrix


LABEL_TO_ID = {label: index for index, label in enumerate(LABELS)}
ID_TO_LABEL = {index: label for label, index in LABEL_TO_ID.items()}
SKLEARN_LABELS = sorted(LABELS)


def build_random_forest() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=400,
        max_depth=5,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )


def build_xgboost() -> XGBClassifier:
    return XGBClassifier(
        objective="multi:softprob",
        num_class=len(LABELS),
        n_estimators=250,
        max_depth=3,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.2,
        reg_lambda=2.0,
        random_state=42,
        n_jobs=-1,
        eval_metric="mlogloss",
    )


def labels_to_ids(labels: np.ndarray) -> np.ndarray:
    return np.array([LABEL_TO_ID[str(label)] for label in labels], dtype=int)


def ids_to_labels(ids: np.ndarray) -> np.ndarray:
    return np.array([ID_TO_LABEL[int(value)] for value in ids], dtype=object)


def classifier_probability_map(
    model: object,
    features: np.ndarray,
    *,
    encoded_labels: bool = False,
) -> dict[str, float]:
    probabilities = model.predict_proba(features)[0]
    classes = model.classes_
    by_label: dict[str, float] = {}
    for class_value, probability in zip(classes, probabilities, strict=True):
        label = (
            ID_TO_LABEL[int(class_value)]
            if encoded_labels
            else str(class_value)
        )
        by_label[label] = float(probability)
    return {label: by_label.get(label, 0.0) for label in LABELS}


def ordered_probabilities(
    model: object,
    features: np.ndarray,
    *,
    encoded_labels: bool = False,
) -> np.ndarray:
    """모델별 class 순서를 고정된 LABELS 순서로 재배열한다."""
    probabilities = model.predict_proba(features)
    classes = [
        ID_TO_LABEL[int(value)] if encoded_labels else str(value)
        for value in model.classes_
    ]
    indices = [classes.index(label) for label in SKLEARN_LABELS]
    return probabilities[:, indices]


def metric_row(
    name: str,
    actual: np.ndarray,
    predicted: np.ndarray,
    probabilities: np.ndarray | None = None,
) -> tuple[str, float, float, float, float | None]:
    loss = None
    if probabilities is not None:
        loss = float(
            log_loss(actual, probabilities, labels=SKLEARN_LABELS)
        )
    return (
        name,
        float(accuracy_score(actual, predicted)),
        float(balanced_accuracy_score(actual, predicted)),
        float(f1_score(actual, predicted, labels=LABELS, average="macro")),
        loss,
    )


def main() -> None:
    rows = load_rows(DATA_PATH)
    split_index = int(len(rows) * TRAIN_RATIO)
    train_rows = rows[:split_index]
    test_rows = rows[split_index:]
    x_train = to_matrix(train_rows, FEATURES)
    x_test = to_matrix(test_rows, FEATURES)
    y_train = make_labels(train_rows)
    y_test = make_labels(test_rows)

    logistic = build_classifier()
    logistic.fit(x_train, y_train)

    forest = build_random_forest()
    forest.fit(x_train, y_train)

    xgboost = build_xgboost()
    y_train_ids = labels_to_ids(y_train)
    sample_weights = compute_sample_weight("balanced", y_train_ids)
    xgboost.fit(x_train, y_train_ids, sample_weight=sample_weights)

    results = [
        metric_row(
            "항상 동결 Baseline",
            y_test,
            np.full(len(y_test), "동결", dtype=object),
        ),
        metric_row(
            "Logistic Regression",
            y_test,
            logistic.predict(x_test),
            ordered_probabilities(logistic, x_test),
        ),
        metric_row(
            "Random Forest",
            y_test,
            forest.predict(x_test),
            ordered_probabilities(forest, x_test),
        ),
        metric_row(
            "XGBoost",
            y_test,
            ids_to_labels(xgboost.predict(x_test)),
            ordered_probabilities(
                xgboost,
                x_test,
                encoded_labels=True,
            ),
        ),
    ]

    print("3개월 뒤 금리 방향 모델 비교 (시간순 80/20 분리)")
    print("-" * 82)
    print(
        f"학습: {train_rows[0]['date']} ~ {train_rows[-1]['date']} "
        f"({len(train_rows)}개), {dict(Counter(y_train))}"
    )
    print(
        f"테스트: {test_rows[0]['date']} ~ {test_rows[-1]['date']} "
        f"({len(test_rows)}개), {dict(Counter(y_test))}"
    )
    print("\n성능")
    print("-" * 82)
    print(
        f"{'모델':<24}{'정확도':>12}{'균형 정확도':>14}"
        f"{'Macro F1':>12}{'Log Loss':>12}"
    )
    for name, accuracy, balanced, macro_f1, loss in results:
        loss_text = "-" if loss is None else f"{loss:.4f}"
        print(
            f"{name:<24}{accuracy:>11.2%}{balanced:>13.2%}"
            f"{macro_f1:>12.4f}{loss_text:>12}"
        )
    print(
        "\n한 번의 시간 분할 결과이므로 최고 점수만 보고 모델을 "
        "선택하면 안 됩니다. 다음 단계는 여러 시점의 순차 검증입니다."
    )


if __name__ == "__main__":
    main()
