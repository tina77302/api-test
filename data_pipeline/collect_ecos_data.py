"""ECOS 실제 월별 데이터를 수집해 금리 예측용 CSV를 만든다.

실행:
    python -m data_pipeline.collect_ecos_data
"""

import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from data_pipeline.ecos_client import PROJECT_DIR, EcosClient, EcosError
from data_pipeline.fred_client import FredClient, FredError


RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "monthly_interest_rate_data.csv"
START_MONTH = "200001"
FRED_SERIES_ID = "FEDFUNDS"


@dataclass(frozen=True)
class SeriesConfig:
    name: str
    stat_code: str
    item_code: str


SERIES = [
    SeriesConfig("current_rate", "722Y001", "0101000"),
    SeriesConfig("cpi_index", "901Y009", "0"),
    SeriesConfig("exchange_rate", "731Y004", "0000001"),
    SeriesConfig("unemployment", "902Y021", "KOR"),
    SeriesConfig("bond_3y", "721Y001", "5020000"),
]


def current_month() -> str:
    today = date.today()
    return f"{today.year:04d}{today.month:02d}"


def save_raw_rows(config: SeriesConfig, rows: list[dict[str, Any]]) -> None:
    """ECOS 원본 응답을 수정하지 않고 JSON 파일로 보관한다."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"ecos_{config.name}.json"
    path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_fred_raw_rows(rows: list[dict[str, Any]]) -> None:
    """FRED 원본 응답을 수정하지 않고 JSON 파일로 보관한다."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / "fred_fedfunds.json"
    path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def rows_to_monthly_values(
    rows: list[dict[str, Any]],
) -> dict[str, float]:
    """ECOS 행에서 YYYY-MM 날짜와 숫자 값만 추출한다."""
    values: dict[str, float] = {}
    for row in rows:
        time_value = str(row.get("TIME", ""))
        data_value = str(row.get("DATA_VALUE", "")).strip()
        if len(time_value) != 6 or not data_value:
            continue
        try:
            values[f"{time_value[:4]}-{time_value[4:]}"] = float(data_value)
        except ValueError:
            continue
    return values


def fred_rows_to_monthly_values(
    rows: list[dict[str, Any]],
) -> dict[str, float]:
    """FRED 관측값을 YYYY-MM 날짜와 숫자 값으로 변환한다."""
    values: dict[str, float] = {}
    for row in rows:
        observation_date = str(row.get("date", ""))
        data_value = str(row.get("value", "")).strip()
        if len(observation_date) < 7 or data_value in {"", "."}:
            continue
        try:
            values[observation_date[:7]] = float(data_value)
        except ValueError:
            continue
    return values


def calculate_yoy_percent(
    monthly_index: dict[str, float],
) -> dict[str, float]:
    """월별 지수에서 전년동월비 상승률을 계산한다."""
    sorted_months = sorted(monthly_index)
    yoy: dict[str, float] = {}
    for month in sorted_months:
        year, month_number = month.split("-")
        previous_month = f"{int(year) - 1:04d}-{month_number}"
        previous_value = monthly_index.get(previous_month)
        current_value = monthly_index[month]
        if previous_value in (None, 0):
            continue
        yoy[month] = (current_value / previous_value - 1) * 100
    return yoy


def add_future_target(
    records: list[dict[str, float | str]],
    months_ahead: int = 3,
) -> list[dict[str, float | str]]:
    """각 행에 months_ahead개월 뒤 기준금리를 목표값으로 추가한다."""
    result: list[dict[str, float | str]] = []
    for index, record in enumerate(records):
        target_index = index + months_ahead
        if target_index >= len(records):
            break
        result.append(
            {
                **record,
                "rate_after_3_months": records[target_index]["current_rate"],
            }
        )
    return result


def save_processed_csv(records: list[dict[str, float | str]]) -> None:
    """병합·변환한 학습 데이터를 CSV로 저장한다."""
    if not records:
        raise EcosError("저장할 처리 데이터가 없습니다.")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "date",
        "current_rate",
        "inflation",
        "exchange_rate",
        "unemployment",
        "bond_3y",
        "us_policy_rate",
        "rate_after_3_months",
    ]
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    client = EcosClient()
    monthly_series: dict[str, dict[str, float]] = {}

    print(f"ECOS 수집 기간: {START_MONTH} ~ {current_month()}")
    for config in SERIES:
        print(f"- {config.name} 수집 중...")
        rows = client.search_statistics(
            stat_code=config.stat_code,
            cycle="M",
            start_date=START_MONTH,
            end_date=current_month(),
            item_code_1=config.item_code,
        )
        save_raw_rows(config, rows)
        monthly_series[config.name] = rows_to_monthly_values(rows)
        print(f"  {len(monthly_series[config.name])}개월 수집")

    print(f"- us_policy_rate({FRED_SERIES_ID}) 수집 중...")
    fred_client = FredClient()
    fred_rows = fred_client.get_observations(
        series_id=FRED_SERIES_ID,
        observation_start=f"{START_MONTH[:4]}-{START_MONTH[4:]}-01",
        observation_end=date.today().isoformat(),
    )
    save_fred_raw_rows(fred_rows)
    monthly_series["us_policy_rate"] = fred_rows_to_monthly_values(fred_rows)
    print(f"  {len(monthly_series['us_policy_rate'])}개월 수집")

    inflation = calculate_yoy_percent(monthly_series.pop("cpi_index"))
    monthly_series["inflation"] = inflation

    # 모든 입력값이 같은 달에 존재하는 공통 월만 사용한다.
    common_months = set.intersection(
        *(set(values) for values in monthly_series.values())
    )
    sorted_months = sorted(common_months)

    records: list[dict[str, float | str]] = []
    for month in sorted_months:
        records.append(
            {
                "date": month,
                "current_rate": monthly_series["current_rate"][month],
                "inflation": monthly_series["inflation"][month],
                "exchange_rate": monthly_series["exchange_rate"][month],
                "unemployment": monthly_series["unemployment"][month],
                "bond_3y": monthly_series["bond_3y"][month],
                "us_policy_rate": monthly_series["us_policy_rate"][month],
            }
        )

    records_with_target = add_future_target(records)
    save_processed_csv(records_with_target)

    print("\n수집 완료")
    print(f"- 공통 월 데이터: {len(records)}개")
    print(f"- 목표값 포함 학습 데이터: {len(records_with_target)}개")
    print(f"- 저장 위치: {OUTPUT_PATH}")
    if records_with_target:
        print(
            f"- 학습 가능 기간: {records_with_target[0]['date']} ~ "
            f"{records_with_target[-1]['date']}"
        )


if __name__ == "__main__":
    try:
        main()
    except (EcosError, FredError) as exc:
        raise SystemExit(f"실제 데이터 수집 실패: {exc}") from exc
