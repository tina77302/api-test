"""3개월 뒤 기준금리 방향(인하·동결·인상)을 분류한다.

실행:
    python -m ml.classify_rate_direction
"""

from collections import Counter

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, log_loss
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.baseline import get_direction, load_rows
from ml.compare_real_models import DATA_PATH, FEATURES, TARGET, to_matrix


LABELS = ["인하", "동결", "인상"]
TRAIN_RATIO = 0.80


def make_labels(rows: list[dict[str, str]]) -> np.ndarray:
    """현재 금리와 3개월 후 금리를 비교해 분류 정답을 만든다."""
    return np.array(
        [
            get_direction(
                float(row["current_rate"]),
                float(row[TARGET]),
            )
            for row in rows
        ],
        dtype=object,
    )


def build_classifier() -> Pipeline:
    """표준화와 다중 로지스틱 회귀를 하나의 모델로 구성한다."""
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(
            class_weight="balanced",
            max_iter=2_000,
            random_state=42,
        ),
    )


def probability_map(
    model: Pipeline,
    features: np.ndarray,
) -> dict[str, float]:
    """한 행의 예측 확률을 인하·동결·인상 순서의 사전으로 반환한다."""
    probabilities = model.predict_proba(features)[0]
    model_classes = model.named_steps["logisticregression"].classes_
    by_class = {
        str(label): float(probability)
        for label, probability in zip(
            model_classes,
            probabilities,
            strict=True,
        )
    }
    return {label: by_class.get(label, 0.0) for label in LABELS}


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
    x_test = to_matrix(test_rows, FEATURES)
    y_train = make_labels(train_rows)
    y_test = make_labels(test_rows)

    model = build_classifier()
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)

    accuracy = float(accuracy_score(y_test, predictions))
    baseline_predictions = np.full(len(y_test), "동결", dtype=object)
    baseline_accuracy = float(accuracy_score(y_test, baseline_predictions))
    loss = float(
        log_loss(
            y_test,
            probabilities,
            labels=list(model.classes_),
        )
    )
    matrix = confusion_matrix(y_test, predictions, labels=LABELS)

    print("3개월 뒤 금리 방향 분류 (시간순 80/20 분리)")
    print("-" * 66)
    print(
        f"학습: {train_rows[0]['date']} ~ {train_rows[-1]['date']} "
        f"({len(train_rows)}개)"
    )
    print(
        f"테스트: {test_rows[0]['date']} ~ {test_rows[-1]['date']} "
        f"({len(test_rows)}개)"
    )
    print(f"학습 정답 분포: {dict(Counter(y_train))}")
    print(f"테스트 정답 분포: {dict(Counter(y_test))}")
    print("\n성능")
    print("-" * 66)
    print(f"항상 동결 Baseline 정확도: {baseline_accuracy:.2%}")
    print(f"로지스틱 회귀 정확도:       {accuracy:.2%}")
    print(f"로지스틱 회귀 Log Loss:     {loss:.4f} (낮을수록 좋음)")
    print("\n혼동행렬 (행=실제, 열=예측)")
    print(f"{'':>8}" + "".join(f"{label:>8}" for label in LABELS))
    for label, values in zip(LABELS, matrix, strict=True):
        print(f"{label:>8}" + "".join(f"{value:>8}" for value in values))
    print(
        "\n주의: class_weight='balanced'는 드문 인하·인상 사례를 더 "
        "강하게 학습하지만, 출력 확률이 실제 발생확률과 정확히 같다는 "
        "뜻은 아닙니다."
    )


if __name__ == "__main__":
    main()
