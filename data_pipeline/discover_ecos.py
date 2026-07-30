"""금리 예측에 필요한 ECOS 통계표와 항목을 키워드로 탐색한다.

실행:
    python -m data_pipeline.discover_ecos
"""

from data_pipeline.ecos_client import EcosClient, EcosError


KEYWORDS = [
    "기준금리",
    "소비자물가",
    "환율",
    "실업률",
    "시장금리",
]
MAX_TABLES_PER_KEYWORD = 8
MAX_ITEMS_PER_TABLE = 12


def main() -> None:
    try:
        client = EcosClient()
        for keyword in KEYWORDS:
            tables = client.search_tables(keyword)
            print(f"\n[{keyword}] 검색 결과: {len(tables)}개")
            print("=" * 72)

            for table in tables[:MAX_TABLES_PER_KEYWORD]:
                print(
                    f"\n통계표: {table.stat_name}\n"
                    f"코드: {table.stat_code} | 주기: {table.cycle} | "
                    f"기관: {table.organization}"
                )

                items = client.list_items(table.stat_code)
                for item in items[:MAX_ITEMS_PER_TABLE]:
                    print(
                        "  - "
                        f"{item.get('ITEM_NAME', '')} "
                        f"(코드={item.get('ITEM_CODE', '')}, "
                        f"레벨={item.get('ITEM_LEVEL', '')}, "
                        f"시작={item.get('START_TIME', '')}, "
                        f"종료={item.get('END_TIME', '')})"
                    )

            if len(tables) > MAX_TABLES_PER_KEYWORD:
                print(
                    f"\n  ... 나머지 "
                    f"{len(tables) - MAX_TABLES_PER_KEYWORD}개 생략"
                )
    except EcosError as exc:
        raise SystemExit(f"ECOS 탐색 실패: {exc}") from exc


if __name__ == "__main__":
    main()
