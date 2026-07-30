"""미국 FRED API의 최소 Python 클라이언트."""

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

FRED_BASE_URL = "https://api.stlouisfed.org/fred"


class FredError(RuntimeError):
    """FRED 요청 또는 응답 처리에 실패한 경우."""


class FredClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("FRED_API_KEY", "")
        if not self.api_key or self.api_key.startswith("your_"):
            raise FredError(".env 파일에 FRED_API_KEY를 설정해주세요.")

    def get_observations(
        self,
        series_id: str,
        observation_start: str,
        observation_end: str,
        frequency: str = "m",
    ) -> list[dict[str, Any]]:
        """FRED 시리즈 관측값을 월별 JSON으로 가져온다."""
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": observation_start,
            "observation_end": observation_end,
            "frequency": frequency,
        }

        try:
            response = httpx.get(
                f"{FRED_BASE_URL}/series/observations",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise FredError(
                f"FRED HTTP 요청에 실패했습니다 "
                f"(상태 코드: {exc.response.status_code})."
            ) from exc
        except httpx.HTTPError as exc:
            # 요청 URL에는 인증키가 포함되므로 원본 예외 문자열을 노출하지 않는다.
            raise FredError(
                "FRED 서버에 연결하지 못했습니다. 네트워크 상태를 확인해주세요."
            ) from exc
        except ValueError as exc:
            raise FredError("FRED 응답이 올바른 JSON이 아닙니다.") from exc

        if "error_code" in payload:
            raise FredError(
                f"FRED 오류 {payload.get('error_code', 'UNKNOWN')}: "
                f"{payload.get('error_message', '알 수 없는 오류')}"
            )

        observations = payload.get("observations", [])
        if not isinstance(observations, list):
            raise FredError("FRED 응답에서 observations를 찾지 못했습니다.")
        return observations
