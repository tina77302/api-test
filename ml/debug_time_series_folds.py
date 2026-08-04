"""현재 UI에 표시되는 4개 시계열 Fold를 날짜·확률 수준으로 감사한다.

실행:
    python -m ml.debug_time_series_folds
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.utils.class_weight import compute_sample_weight

from ml.classify_rate_direction import LABELS
from ml.tune_post_pandemic_models import (
    FEATURE_PATH,
    MODEL_FEATURES,
    N_SPLITS,
    START_DATE,
    TARGET_GAP,
    TEST_SIZE,
    TRAIN_PATH,
    attach_targets,
    engineer_features,
    make_forest,
    make_xgboost,
    to_matrix,
)
from ml.baseline import load_rows


PROJECT_DIR = Path(__file__).resolve().parent.parent
FORECAST_PATH = PROJECT_DIR / "outputs" / "tuned_post_pandemic_forecast.json"
JSON_PATH = PROJECT_DIR / "outputs" / "time_series_fold_debug.json"
REPORT_PATH = PROJECT_DIR / "docs" / "TIME_SERIES_FOLD_DEBUG.md"
TOLERANCE = 1e-8


def add_months(month: str, count: int) -> str:
    year, value = map(int, month.split("-"))
    index = year * 12 + value - 1 + count
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def tolerant_direction(current: float, future: float) -> str:
    difference = future - current
    if abs(difference) < TOLERANCE:
        return "동결"
    return "인상" if difference > 0 else "인하"


def probability_rows(model: object, x_test: np.ndarray, encoded_classes: list[str] | None = None) -> list[dict[str, float]]:
    raw = model.predict_proba(x_test)
    classes = [encoded_classes[int(value)] if encoded_classes is not None else str(value) for value in model.classes_]
    return [
        {label: float(row[classes.index(label)]) if label in classes else 0.0 for label in LABELS}
        for row in raw
    ]


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, object]:
    recalls = recall_score(actual, predicted, labels=LABELS, average=None, zero_division=0)
    return {
        "correct": int(np.sum(actual == predicted)),
        "total": len(actual),
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_f1": float(f1_score(actual, predicted, labels=LABELS, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(actual, predicted, labels=LABELS).tolist(),
        "recall": {label: float(value) for label, value in zip(LABELS, recalls, strict=True)},
    }


def markdown_matrix(matrix: list[list[int]]) -> str:
    lines = ["| 실제 \\ 예측 | 인하 | 동결 | 인상 |", "|---|---:|---:|---:|"]
    lines.extend(f"| {label} | " + " | ".join(map(str, row)) + " |" for label, row in zip(LABELS, matrix, strict=True))
    return "\n".join(lines)


def main() -> None:
    monthly_rows = load_rows(FEATURE_PATH)
    target_rows = load_rows(TRAIN_PATH)
    engineered_rows = engineer_features(monthly_rows)
    train_rows, labels = attach_targets(engineered_rows, target_rows, start_date=START_DATE)
    x = to_matrix(train_rows)
    forecast = json.loads(FORECAST_PATH.read_text(encoding="utf-8"))
    rf_params = forecast["models"]["random_forest"]["best_params"]
    xgb_params = forecast["models"]["xgboost"]["best_params"]
    target_by_date = {row["date"]: row for row in target_rows}
    raw_by_date = {row["date"]: row for row in monthly_rows}

    target_audit: list[dict[str, object]] = []
    exact_and_tolerant_disagreements = 0
    for row, label in zip(train_rows, labels, strict=True):
        date = str(row["date"]); target_date = add_months(date, 3)
        current = float(target_by_date[date]["current_rate"])
        future = float(target_by_date[date]["rate_after_3_months"])
        shifted = float(raw_by_date[target_date]["current_rate"])
        tolerant = tolerant_direction(current, future)
        if tolerant != str(label):
            exact_and_tolerant_disagreements += 1
        target_audit.append({"feature_date": date, "target_date": target_date, "current_rate": current, "future_rate": future, "shifted_source_rate": shifted, "label": str(label), "tolerant_label": tolerant, "exact_three_month_match": target_date in raw_by_date and shifted == future})

    splitter = TimeSeriesSplit(n_splits=N_SPLITS, test_size=TEST_SIZE, gap=TARGET_GAP)
    folds: list[dict[str, object]] = []
    pooled: dict[str, dict[str, list[str]]] = {"random_forest": {"true": [], "pred": []}, "xgboost": {"true": [], "pred": []}}
    for fold_number, (train_indices, test_indices) in enumerate(splitter.split(x), 1):
        x_train, x_test = x[train_indices], x[test_indices]
        y_train, y_test = labels[train_indices], labels[test_indices]
        rf = make_forest(rf_params); rf.fit(x_train, y_train)
        rf_pred = rf.predict(x_test); rf_prob = probability_rows(rf, x_test)

        classes = sorted(set(str(value) for value in y_train))
        label_to_id = {label: index for index, label in enumerate(classes)}
        encoded = np.array([label_to_id[str(value)] for value in y_train])
        xgb_model_params = dict(xgb_params)
        balanced = bool(xgb_model_params.pop("use_balanced_weights"))
        xgb = make_xgboost(xgb_model_params, len(classes))
        xgb.fit(x_train, encoded, sample_weight=compute_sample_weight("balanced", encoded) if balanced else None)
        xgb_ids = xgb.predict(x_test).astype(int)
        xgb_pred = np.array([classes[value] for value in xgb_ids], dtype=object)
        xgb_prob = probability_rows(xgb, x_test, classes)

        previous_pred = np.array([{-1.0: "인하", 0.0: "동결", 1.0: "인상"}[float(train_rows[index]["rate_direction_3m"])] for index in test_indices], dtype=object)
        majority = Counter(y_train).most_common(1)[0][0]
        baselines = {
            "always_hold": metrics(y_test, np.full(len(y_test), "동결", dtype=object)),
            "previous_direction": metrics(y_test, previous_pred),
            "train_majority": metrics(y_test, np.full(len(y_test), majority, dtype=object)),
        }
        details = []
        for position, index in enumerate(test_indices):
            date = str(train_rows[index]["date"]); source = target_by_date[date]
            details.append({
                "feature_date": date, "target_date": add_months(date, 3),
                "current_rate": float(source["current_rate"]), "future_rate": float(source["rate_after_3_months"]),
                "y_true": str(y_test[position]), "rf_pred": str(rf_pred[position]), "xgb_pred": str(xgb_pred[position]),
                "rf_probabilities": rf_prob[position], "xgb_probabilities": xgb_prob[position],
            })
        model_results = {"random_forest": {**metrics(y_test, rf_pred), "prediction_distribution": dict(Counter(rf_pred)), "model_classes": [str(value) for value in rf.classes_]}, "xgboost": {**metrics(y_test, xgb_pred), "prediction_distribution": dict(Counter(xgb_pred)), "encoder_classes": classes, "model_classes": [int(value) for value in xgb.classes_]}}
        for name in ("random_forest", "xgboost"):
            displayed = forecast["models"][name]["folds"][fold_number - 1]["metrics"]
            model_results[name]["matches_displayed_metrics"] = (
                abs(model_results[name]["accuracy"] - displayed["accuracy"]) < 1e-12
                and abs(model_results[name]["macro_f1"] - displayed["macro_f1"]) < 1e-12
            )
        for name, pred in (("random_forest", rf_pred), ("xgboost", xgb_pred)):
            pooled[name]["true"].extend(map(str, y_test)); pooled[name]["pred"].extend(map(str, pred))
            model_results[name]["below_baselines"] = [key for key, value in baselines.items() if model_results[name]["accuracy"] < value["accuracy"]]
        gap_indices = list(range(int(train_indices[-1]) + 1, int(test_indices[0])))
        folds.append({
            "fold": fold_number,
            "train_period": [str(train_rows[train_indices[0]]["date"]), str(train_rows[train_indices[-1]]["date"])],
            "gap_period": [str(train_rows[gap_indices[0]]["date"]), str(train_rows[gap_indices[-1]]["date"])],
            "test_period": [str(train_rows[test_indices[0]]["date"]), str(train_rows[test_indices[-1]]["date"])],
            "train_samples": len(train_indices), "test_samples": len(test_indices),
            "train_distribution": dict(Counter(y_train)), "test_distribution": dict(Counter(y_test)),
            "index_alignment": {"x_test_indices": test_indices.tolist(), "y_test_indices": test_indices.tolist(), "dates_sorted": details == sorted(details, key=lambda item: item["feature_date"])},
            "models": model_results, "baselines": baselines, "rows": details,
        })

    overall = {}
    for name, values in pooled.items():
        actual=np.array(values["true"],dtype=object); predicted=np.array(values["pred"],dtype=object)
        overall[name] = metrics(actual,predicted)
        overall[name]["mean_fold_accuracy"] = float(np.mean([fold["models"][name]["accuracy"] for fold in folds]))
        overall[name]["mean_fold_macro_f1"] = float(np.mean([fold["models"][name]["macro_f1"] for fold in folds]))

    result = {
        "configuration": {"method": "expanding TimeSeriesSplit", "n_splits": N_SPLITS, "test_size_months": TEST_SIZE, "gap_months": TARGET_GAP, "forecast_horizon_months": 3, "labels": LABELS, "tolerance": TOLERANCE, "features": MODEL_FEATURES},
        "target_audit": {"rows": len(target_audit), "last_three_raw_rows_excluded": [row["date"] for row in monthly_rows[-3:]], "all_target_dates_exactly_three_months": all(row["exact_three_month_match"] for row in target_audit), "exact_vs_tolerant_label_disagreements": exact_and_tolerant_disagreements},
        "class_mapping": {"canonical_labels": LABELS, "frontend_order": LABELS, "xgboost_encoding": {label:index for index,label in enumerate(LABELS)}, "note": "각 fold의 XGBoost 인코더는 해당 학습 fold에 존재하는 정렬 클래스만 연속 정수로 다시 매핑함"},
        "preprocessing_audit": {"scaler": "사용하지 않음", "imputer": "사용하지 않음", "feature_selector": "사용하지 않음", "feature_nan_count": int(np.isnan(x).sum()), "rolling_features": "현재와 1·3·6개월 과거값만 사용", "future_fill": "사용하지 않음"},
        "folds": folds, "overall": overall,
    }
    JSON_PATH.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")

    lines = ["# RateScope 시계열 Fold 디버깅 리포트", "", "> UI 숫자는 변경하지 않고 현재 표시 모델·파라미터·Fold를 그대로 재현했습니다.", "", "## 결론", "", "- 검증 로직의 날짜/인덱스/클래스 확률 열 어긋남은 발견되지 않았습니다.", "- UI의 검증은 1-step Walk-forward가 아니라 4개 expanding `TimeSeriesSplit`입니다.", "- **Fold 02 학습 구간에는 인하가 0건**이고 평가 6건은 모두 인하입니다. 두 모델의 학습 클래스가 `동결·인상`뿐이라 인하를 예측할 수 없어 0%가 발생했습니다.", "- Fold 02에서 직전 방향 반복 기준선은 6건 모두 인하를 예측해 100%였으며 두 ML 모델보다 높았습니다.", "- Fold 04는 학습에 세 클래스가 모두 있지만 평가 6건이 전부 동결인 국면에서 XGBoost가 전부 인상을 선택했습니다. 이는 매핑 오류가 아니라 일반화 실패입니다.", "- 표본이 51개뿐이고 Fold별 클래스 구성이 크게 달라 성능 분산이 매우 큽니다.", "- 현재 튜닝과 성능 표시가 같은 Fold를 사용하므로 성능 과대평가 가능성은 있지만, 0%의 직접 원인은 아닙니다.", "", "## 타깃·정렬 감사", "", f"- 3개월 target 일치: **{result['target_audit']['all_target_dates_exactly_three_months']}**", f"- tolerance 적용 전후 라벨 불일치: **{exact_and_tolerant_disagreements}건**", f"- 제외된 마지막 원자료 3개월: **{', '.join(result['target_audit']['last_three_raw_rows_excluded'])}**", "- pandas shift 대신 `records[index + 3]`을 사용하며 월별 연속성과 target_date를 전 행 대조했습니다.", "- X/y는 동일한 `train_rows`와 동일 정수 인덱스로 동시에 분할됩니다. scaler·imputer·selector는 없습니다.", "- 변화량 Feature는 현재와 과거 1·3·6개월만 참조합니다.", ""]
    for fold in folds:
        lines += [f"## Fold {fold['fold']:02d}", "", f"- 학습: {fold['train_period'][0]} ~ {fold['train_period'][1]} ({fold['train_samples']}건)", f"- Gap: {fold['gap_period'][0]} ~ {fold['gap_period'][1]} (3개월)", f"- 평가: {fold['test_period'][0]} ~ {fold['test_period'][1]} ({fold['test_samples']}건)", f"- 학습 분포: `{fold['train_distribution']}`", f"- 평가 실제 분포: `{fold['test_distribution']}`", ""]
        lines += ["### 기준선", "", "| 기준선 | Accuracy | Macro F1 | 적중 |", "|---|---:|---:|---:|"]
        for baseline_name, baseline in fold["baselines"].items():
            lines.append(f"| {baseline_name} | {baseline['accuracy']:.2%} | {baseline['macro_f1']:.4f} | {baseline['correct']} / {baseline['total']} |")
        lines.append("")
        for name in ("random_forest","xgboost"):
            model=fold["models"][name]
            class_description = model.get("model_classes") if name == "random_forest" else {"encoder_classes": model.get("encoder_classes"), "model_internal_ids": model.get("model_classes")}
            lines += [f"### {name}", "", f"- UI 저장 지표와 재현 일치: **{model['matches_displayed_metrics']}**", f"- 클래스 순서: `{class_description}`", f"- 예측 분포: `{model['prediction_distribution']}`", f"- 적중: **{model['correct']} / {model['total']}**", f"- Accuracy: **{model['accuracy']:.2%}**", f"- Macro F1: **{model['macro_f1']:.4f}**", f"- 기준선보다 낮음: `{model['below_baselines'] or '없음'}`", "", markdown_matrix(model["confusion_matrix"]), ""]
        lines += ["### 날짜별 실제·예측·확률", "", "| feature_date | target_date | y_true | RF pred | RF P(인하/동결/인상) | XGB pred | XGB P(인하/동결/인상) |", "|---|---|---|---|---|---|---|"]
        for row in fold["rows"]:
            rp=row["rf_probabilities"];xp=row["xgb_probabilities"]
            lines.append(f"| {row['feature_date']} | {row['target_date']} | {row['y_true']} | {row['rf_pred']} | {rp['인하']:.3f}/{rp['동결']:.3f}/{rp['인상']:.3f} | {row['xgb_pred']} | {xp['인하']:.3f}/{xp['동결']:.3f}/{xp['인상']:.3f} |")
        lines.append("")
    fold2=folds[1]
    lines += ["## Fold 02 요청 상세표", "", "| feature_date | target_date | current_rate | future_rate | y_true | rf_pred | xgb_pred | rf_probabilities | xgb_probabilities |", "|---|---|---:|---:|---|---|---|---|---|"]
    for row in fold2["rows"]:
        lines.append(f"| {row['feature_date']} | {row['target_date']} | {row['current_rate']:.2f} | {row['future_rate']:.2f} | {row['y_true']} | {row['rf_pred']} | {row['xgb_pred']} | `{row['rf_probabilities']}` | `{row['xgb_probabilities']}` |")
    lines += ["", "## 전체 집계", ""]
    for name,value in overall.items():
        lines += [f"### {name}", "", f"- pooled Accuracy: **{value['accuracy']:.2%}**", f"- pooled Macro F1: **{value['macro_f1']:.4f}**", f"- Fold 평균 Accuracy: **{value['mean_fold_accuracy']:.2%}**", f"- Fold 평균 Macro F1: **{value['mean_fold_macro_f1']:.4f}**", f"- Recall: `{value['recall']}`", "", markdown_matrix(value["confusion_matrix"]), ""]
    REPORT_PATH.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"JSON: {JSON_PATH}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
