"""현재 월의 잠정 경제지표를 수집해 실시간 예측 입력을 만든다.

실행:
    python -m data_pipeline.collect_live_features
"""

import json
from datetime import date, timedelta
from pathlib import Path
from statistics import fmean
from typing import Any

from data_pipeline.collect_ecos_data import (
    calculate_yoy_percent,
    fred_rows_to_monthly_values,
    rows_to_monthly_values,
)
from data_pipeline.ecos_client import PROJECT_DIR, EcosClient, EcosError
from data_pipeline.fred_client import FredClient, FredError


LIVE_DIR = PROJECT_DIR / "data" / "live"
OUTPUT_PATH = LIVE_DIR / "latest_features.json"


def shift_month(year: int, month: int, offset: int) -> str:
    """year/month에서 offset개월 이동한 YYYYMM 문자열을 반환한다."""
    zero_based = year * 12 + (month - 1) + offset
    shifted_year, shifted_month = divmod(zero_based, 12)
    return f"{shifted_year:04d}{shifted_month + 1:02d}"


def numeric_ecos_rows(rows: list[dict[str, Any]]) -> list[tuple[str, float]]:
    values: list[tuple[str, float]] = []
    for row in rows:
        time_value = str(row.get("TIME", ""))
        data_value = str(row.get("DATA_VALUE", "")).strip()
        if not time_value or not data_value:
            continue
        try:
            values.append((time_value, float(data_value)))
        except ValueError:
            continue
    return sorted(values)


def latest_value(
    values: list[tuple[str, float]],
    name: str,
) -> tuple[str, float]:
    if not values:
        raise EcosError(f"{name}의 최신 값을 찾지 못했습니다.")
    return values[-1]


def average_value(
    values: list[tuple[str, float]],
    name: str,
) -> tuple[str, str, float]:
    if not values:
        raise EcosError(f"{name}의 월중 값을 찾지 못했습니다.")
    return values[0][0], values[-1][0], fmean(value for _, value in values)


def main() -> None:
    today = date.today()
    month_start_daily = f"{today.year:04d}{today.month:02d}01"
    today_daily = today.strftime("%Y%m%d")
    current_month = today.strftime("%Y%m")
    # 확정 월별 물가는 현재 월보다 1~2개월 늦게 발표될 수 있다.
    # 전년동월비 계산에 필요한 전년도 관측치까지 항상 포함한다.
    cpi_start_month = shift_month(today.year, today.month, -24)

    ecos = EcosClient()
    fred = FredClient()

    print(f"잠정 데이터 기준일: {today.isoformat()}")

    policy_rows = ecos.search_statistics(
        "722Y001",
        "D",
        month_start_daily,
        today_daily,
        "0101000",
    )
    policy_date, current_rate = latest_value(
        numeric_ecos_rows(policy_rows),
        "한국은행 기준금리",
    )

    exchange_rows = ecos.search_statistics(
        "731Y001",
        "D",
        month_start_daily,
        today_daily,
        "0000001",
    )
    exchange_start, exchange_end, exchange_rate = average_value(
        numeric_ecos_rows(exchange_rows),
        "원/미국달러 환율",
    )

    bond_rows = ecos.search_statistics(
        "817Y002",
        "D",
        month_start_daily,
        today_daily,
        "010200000",
    )
    bond_start, bond_end, bond_3y = average_value(
        numeric_ecos_rows(bond_rows),
        "국고채 3년",
    )

    cpi_rows = ecos.search_statistics(
        "901Y009",
        "M",
        cpi_start_month,
        current_month,
        "0",
    )
    cpi_values = rows_to_monthly_values(cpi_rows)
    inflation_values = calculate_yoy_percent(cpi_values)
    if not inflation_values:
        raise EcosError("소비자물가 전년동월비를 계산하지 못했습니다.")
    inflation_month = sorted(inflation_values)[-1]
    inflation = inflation_values[inflation_month]

    unemployment_rows = ecos.search_statistics(
        "902Y021",
        "M",
        f"{today.year - 1:04d}01",
        current_month,
        "KOR",
    )
    unemployment_values = rows_to_monthly_values(unemployment_rows)
    if not unemployment_values:
        raise EcosError("한국 실업률 최신값을 찾지 못했습니다.")
    unemployment_month = sorted(unemployment_values)[-1]
    unemployment = unemployment_values[unemployment_month]

    fred_rows = fred.get_observations(
        series_id="DFF",
        # 월초나 휴일에는 이번 달 DFF가 아직 게시되지 않을 수 있다.
        # 직전 공개 영업일을 포함하도록 최근 14일을 조회한다.
        observation_start=(today - timedelta(days=14)).isoformat(),
        observation_end=today.isoformat(),
        frequency="d",
    )
    fred_values = [
        (str(row.get("date", "")), float(row["value"]))
        for row in fred_rows
        if str(row.get("value", "")) not in {"", "."}
    ]
    if not fred_values:
        raise FredError("DFF의 현재 월 값을 찾지 못했습니다.")
    fred_start = fred_values[0][0]
    fred_end = fred_values[-1][0]
    us_policy_rate = fmean(value for _, value in fred_values)

    output = {
        "as_of_date": today.isoformat(),
        "status": "partial_current_month",
        "target": "Korea policy rate three months ahead",
        "features": {
            "current_rate": round(current_rate, 4),
            "inflation": round(inflation, 4),
            "exchange_rate": round(exchange_rate, 4),
            "unemployment": round(unemployment, 4),
            "bond_3y": round(bond_3y, 4),
            "us_policy_rate": round(us_policy_rate, 4),
        },
        "source_periods": {
            "current_rate": policy_date,
            "inflation": inflation_month,
            "exchange_rate": f"{exchange_start}~{exchange_end}",
            "unemployment": unemployment_month,
            "bond_3y": f"{bond_start}~{bond_end}",
            "us_policy_rate": f"{fred_start}~{fred_end}",
        },
        "notes": [
            "현재 월이 끝나기 전의 잠정 입력값입니다.",
            "환율·국고채·미국 금리는 월초부터 기준일까지의 평균입니다.",
            "물가와 실업률은 이용 가능한 최신 확정 월 자료입니다.",
            "학습 데이터가 아니라 실시간 추론 입력으로만 사용합니다.",
        ],
    }

    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"저장 위치: {OUTPUT_PATH}")
    print("입력값:")
    for name, value in output["features"].items():
        print(f"- {name}: {value}")
    print("출처 기간:")
    for name, period in output["source_periods"].items():
        print(f"- {name}: {period}")


if __name__ == "__main__":
    try:
        main()
    except (EcosError, FredError) as exc:
        raise SystemExit(f"잠정 데이터 수집 실패: {exc}") from exc
