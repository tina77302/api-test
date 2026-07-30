"""연습용 기준금리 데이터로 baseline 모델을 평가한다.

이 실습의 baseline 규칙:
    3개월 후 예상 기준금리 = 현재 기준금리

실행:
    python ml/baseline.py
"""

import csv
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_DIR / "data" / "sample_interest_rates.csv"


def predict_baseline(current_rate: float) -> float:
    """현재 금리가 3개월 후에도 유지된다고 예측한다."""
    return current_rate


def get_direction(current_rate: float, future_rate: float) -> str:
    """현재 금리와 미래 금리를 비교해 인상·동결·인하로 변환한다."""
    if future_rate > current_rate:
        return "인상"
    if future_rate < current_rate:
        return "인하"
    return "동결"


def load_rows(path: Path) -> list[dict[str, str]]:
    """CSV 파일을 읽어 행 목록으로 반환한다."""
    with path.open(encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def mean_absolute_error(actual: list[float], predicted: list[float]) -> float:
    """실제값과 예측값의 평균 절대 오차(MAE)를 계산한다."""
    if len(actual) != len(predicted):
        raise ValueError("실제값과 예측값의 개수가 같아야 합니다.")
    if not actual:
        raise ValueError("평가할 데이터가 없습니다.")

    absolute_errors = [
        abs(actual_value - predicted_value)
        for actual_value, predicted_value in zip(actual, predicted, strict=True)
    ]
    return sum(absolute_errors) / len(absolute_errors)


def evaluate() -> None:
    """전체 연습 데이터를 대상으로 baseline 성능을 출력한다."""
    rows = load_rows(DATA_PATH)

    actual_rates: list[float] = []
    predicted_rates: list[float] = []
    correct_directions = 0

    print("날짜       현재금리  실제(3개월 후)  예측값  실제방향  예측방향")
    print("-" * 67)

    for row in rows:
        current_rate = float(row["current_rate"])
        actual_rate = float(row["rate_after_3_months"])
        predicted_rate = predict_baseline(current_rate)

        actual_direction = get_direction(current_rate, actual_rate)
        predicted_direction = get_direction(current_rate, predicted_rate)

        actual_rates.append(actual_rate)
        predicted_rates.append(predicted_rate)
        if actual_direction == predicted_direction:
            correct_directions += 1

        print(
            f"{row['date']}    "
            f"{current_rate:>5.2f}%       "
            f"{actual_rate:>5.2f}%       "
            f"{predicted_rate:>5.2f}%    "
            f"{actual_direction:^6}    "
            f"{predicted_direction:^6}"
        )

    mae = mean_absolute_error(actual_rates, predicted_rates)
    direction_accuracy = correct_directions / len(rows)

    print("\n평가 결과")
    print("-" * 30)
    print(f"평가 데이터 수: {len(rows)}개")
    print(f"MAE: {mae:.4f}%p")
    print(f"방향 정확도: {direction_accuracy:.2%}")
    print("\n해석:")
    print(f"- baseline은 평균적으로 실제 금리와 {mae:.4f}%p 차이가 났습니다.")
    print(
        f"- 인상·동결·인하 방향은 전체의 "
        f"{direction_accuracy:.2%}를 맞혔습니다."
    )


if __name__ == "__main__":
    evaluate()
