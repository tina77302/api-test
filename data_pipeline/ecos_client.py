"""한국은행 ECOS Open API의 최소 Python 클라이언트."""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

ECOS_BASE_URL = "https://ecos.bok.or.kr/api"


class EcosError(RuntimeError):
    """ECOS가 오류 응답을 반환했거나 응답 구조가 잘못된 경우."""


@dataclass(frozen=True)
class EcosTable:
    stat_code: str
    stat_name: str
    cycle: str
    organization: str


class EcosClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("BOK_ECOS_API_KEY", "")
        if not self.api_key or self.api_key.startswith("your_"):
            raise EcosError(
                ".env 파일에 BOK_ECOS_API_KEY를 설정해주세요."
            )

    def _request(
        self,
        service: str,
        *path_parts: str,
        start_index: int = 1,
        end_index: int = 10_000,
    ) -> dict[str, Any]:
        encoded_parts = "/".join(quote(part, safe="") for part in path_parts)
        url = (
            f"{ECOS_BASE_URL}/{service}/{self.api_key}/json/kr/"
            f"{start_index}/{end_index}"
        )
        if encoded_parts:
            url = f"{url}/{encoded_parts}"

        for attempt in range(3):
            try:
                response = httpx.get(url, timeout=30.0)
                response.raise_for_status()
                payload = response.json()
                break
            except httpx.HTTPStatusError as exc:
                retryable = exc.response.status_code >= 500
                if retryable and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise EcosError(
                    f"ECOS HTTP 요청에 실패했습니다 "
                    f"(상태 코드: {exc.response.status_code})."
                ) from exc
            except httpx.HTTPError as exc:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                # 요청 URL에는 인증키가 포함되므로 원본 예외 문자열을 노출하지 않는다.
                raise EcosError(
                    "ECOS 서버에 연결하지 못했습니다. 네트워크 상태를 확인해주세요."
                ) from exc
            except ValueError as exc:
                raise EcosError("ECOS 응답이 올바른 JSON이 아닙니다.") from exc

        if "RESULT" in payload:
            result = payload["RESULT"]
            raise EcosError(
                f"ECOS 오류 {result.get('CODE', 'UNKNOWN')}: "
                f"{result.get('MESSAGE', '알 수 없는 오류')}"
            )
        return payload

    def list_tables(self) -> list[EcosTable]:
        """ECOS에서 검색 가능한 통계표 목록을 가져온다."""
        payload = self._request("StatisticTableList")
        service_data = payload.get("StatisticTableList", {})
        rows = service_data.get("row", [])
        if not isinstance(rows, list):
            raise EcosError("통계표 목록 응답에서 row를 찾지 못했습니다.")

        tables: list[EcosTable] = []
        for row in rows:
            if row.get("SRCH_YN") != "Y":
                continue
            tables.append(
                EcosTable(
                    stat_code=str(row.get("STAT_CODE", "")),
                    stat_name=str(row.get("STAT_NAME", "")),
                    cycle=str(row.get("CYCLE", "")),
                    organization=str(row.get("ORG_NAME", "")),
                )
            )
        return tables

    def search_tables(self, keyword: str) -> list[EcosTable]:
        """통계표 이름에 keyword가 들어간 검색 가능 통계표를 찾는다."""
        normalized_keyword = keyword.casefold().strip()
        return [
            table
            for table in self.list_tables()
            if normalized_keyword in table.stat_name.casefold()
        ]

    def list_items(self, stat_code: str) -> list[dict[str, Any]]:
        """통계표에서 선택 가능한 세부 항목 목록을 가져온다."""
        payload = self._request("StatisticItemList", stat_code)
        service_data = payload.get("StatisticItemList", {})
        rows = service_data.get("row", [])
        if not isinstance(rows, list):
            raise EcosError("통계 항목 응답에서 row를 찾지 못했습니다.")
        return rows

    def search_statistics(
        self,
        stat_code: str,
        cycle: str,
        start_date: str,
        end_date: str,
        item_code_1: str,
        item_code_2: str = "",
        item_code_3: str = "",
        item_code_4: str = "",
    ) -> list[dict[str, Any]]:
        """선택한 통계표와 항목의 시계열 값을 조회한다."""
        payload = self._request(
            "StatisticSearch",
            stat_code,
            cycle,
            start_date,
            end_date,
            item_code_1,
            item_code_2,
            item_code_3,
            item_code_4,
        )
        service_data = payload.get("StatisticSearch", {})
        rows = service_data.get("row", [])
        if not isinstance(rows, list):
            raise EcosError("통계 조회 응답에서 row를 찾지 못했습니다.")
        return rows
