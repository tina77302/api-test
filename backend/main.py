import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path as ApiPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, Response
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field


PROJECT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
load_dotenv(PROJECT_DIR / ".env")

app = FastAPI(
    title="My FastAPI Backend",
    description=(
        "사용자 Mock 데이터 조회·등록과 OpenAI 채팅 기능을 제공하는 API입니다.\n\n"
        "### 사용 순서\n"
        "1. `GET /health`로 서버 상태를 확인합니다.\n"
        "2. 사용자 API는 별도 인증 없이 테스트할 수 있습니다.\n"
        "3. 채팅 API를 사용하려면 `.env`에 `OPENAI_API_KEY`를 설정합니다.\n\n"
        "> 사용자 데이터는 메모리에만 저장되므로 서버를 재시작하면 초기화됩니다."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "API 관리자",
        "email": "admin@example.com",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "honggildong",
                "email": "hong@example.com",
                "age": 25,
            }
        }
    )

    username: str = Field(
        min_length=2,
        max_length=50,
        description="사용자 이름",
        examples=["honggildong"],
    )
    email: str = Field(
        min_length=5,
        max_length=254,
        description="이메일 주소",
        examples=["hong@example.com"],
    )
    age: int | None = Field(
        default=None,
        ge=0,
        le=150,
        description="나이",
        examples=[25],
    )


class UserResponse(UserCreate):
    id: int = Field(description="사용자 고유 ID", examples=[1])


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "FastAPI가 무엇인지 한 문장으로 설명해줘.",
            }
        }
    )

    message: str = Field(
        min_length=1,
        max_length=10_000,
        description="OpenAI 모델에 전달할 메시지",
    )


class ChatResponse(BaseModel):
    answer: str = Field(description="OpenAI 모델이 생성한 답변")
    model: str = Field(description="답변 생성에 사용한 모델")


def read_json_file(path: Path) -> dict:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="예측 결과가 없습니다. 자동 업데이트를 먼저 실행해주세요.",
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(
            status_code=500,
            detail="예측 결과 파일을 읽을 수 없습니다.",
        ) from exc


def generate_mock_users() -> list[dict[str, object]]:
    return [
        {
            "id": user_id,
            "username": f"user{user_id}",
            "email": f"user{user_id}@example.com",
            "age": random.randint(18, 60),
        }
        for user_id in range(1, 31)
    ]


db_users = generate_mock_users()


@app.get(
    "/",
    include_in_schema=False,
)
async def frontend_home() -> HTMLResponse:
    return HTMLResponse(
        (FRONTEND_DIR / "index.html").read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/static/styles.css", include_in_schema=False)
async def frontend_styles() -> Response:
    return Response(
        (FRONTEND_DIR / "styles.css").read_bytes(),
        media_type="text/css",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@app.get("/static/app.js", include_in_schema=False)
async def frontend_script() -> Response:
    return Response(
        (FRONTEND_DIR / "app.js").read_bytes(),
        media_type="text/javascript",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@app.get("/static/prediction_history.js", include_in_schema=False)
async def prediction_history_script() -> Response:
    return Response(
        (FRONTEND_DIR / "prediction_history.js").read_bytes(),
        media_type="text/javascript",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@app.get(
    "/health",
    tags=["시스템"],
    summary="서버 상태 확인",
    response_description="서버가 정상이면 `ok`를 반환합니다.",
)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/forecast/latest",
    tags=["금리 예측"],
    summary="최신 3개월 기준금리 방향 예측",
    description=(
        "포스트 팬데믹 데이터와 시차 특성으로 튜닝한 Random Forest, "
        "XGBoost 및 두 모델 평균 확률을 반환합니다."
    ),
)
async def latest_forecast() -> dict:
    return read_json_file(
        PROJECT_DIR / "outputs" / "tuned_post_pandemic_forecast.json"
    )


@app.get(
    "/forecast/reliability",
    tags=["금리 예측"],
    summary="신뢰도 개선 데이터 설계 모델",
    description=(
        "2008년 이후 자료, 최근 가중치, 계층형 분류와 중첩 "
        "시계열 검증을 적용한 실험 결과를 반환합니다."
    ),
)
async def reliability_forecast() -> dict:
    return read_json_file(
        PROJECT_DIR / "outputs" / "reliability_forecast.json"
    )


@app.get(
    "/forecast/history",
    tags=["금리 예측"],
    summary="최근 기준금리와 경제지표 이력",
)
async def forecast_history(months: int = 36) -> dict:
    months = min(max(months, 6), 360)
    path = (
        PROJECT_DIR
        / "data"
        / "processed"
        / "monthly_interest_rate_features.csv"
    )
    if not path.exists():
        raise HTTPException(status_code=503, detail="월별 데이터가 없습니다.")
    import csv

    with path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))[-months:]
    return {"months": len(rows), "rows": rows}


@app.get(
    "/forecast/status",
    tags=["금리 예측"],
    summary="예측 데이터 업데이트 상태",
)
async def forecast_status() -> dict:
    forecast_path = (
        PROJECT_DIR / "outputs" / "tuned_post_pandemic_forecast.json"
    )
    update_path = PROJECT_DIR / "outputs" / "update_status.json"
    response = {
        "forecast_available": forecast_path.exists(),
        "forecast_updated_at": None,
        "automation": None,
    }
    if forecast_path.exists():
        modified = datetime.fromtimestamp(
            forecast_path.stat().st_mtime,
            tz=timezone.utc,
        )
        response["forecast_updated_at"] = modified.isoformat()
    if update_path.exists():
        response["automation"] = read_json_file(update_path)
    return response


@app.get(
    "/prediction-history",
    tags=["금리 예측"],
    summary="과거 예측과 실제 결정 비교",
)
async def prediction_history() -> dict:
    return read_json_file(PROJECT_DIR / "data" / "prediction_history.json")


@app.get(
    "/users",
    response_model=list[UserResponse],
    tags=["사용자"],
    summary="전체 사용자 조회",
    description="메모리에 저장된 모든 Mock 사용자를 반환합니다.",
    response_description="사용자 목록",
)
async def get_users() -> list[dict[str, object]]:
    return db_users


@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
    tags=["사용자"],
    summary="사용자 단건 조회",
    description="사용자 ID와 일치하는 사용자 한 명을 조회합니다.",
    responses={
        404: {
            "description": "해당 ID의 사용자가 존재하지 않음",
            "content": {
                "application/json": {
                    "example": {"detail": "사용자를 찾을 수 없습니다."}
                }
            },
        }
    },
)
async def get_user(
    user_id: Annotated[int, ApiPath(ge=1, description="조회할 사용자 ID")],
) -> dict[str, object]:
    for user in db_users:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")


@app.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
    tags=["사용자"],
    summary="사용자 등록",
    description="새로운 사용자를 메모리에 등록하고 생성된 사용자 정보를 반환합니다.",
    response_description="생성된 사용자",
)
async def create_user(user: UserCreate) -> dict[str, object]:
    new_user = {
        "id": max((int(item["id"]) for item in db_users), default=0) + 1,
        **user.model_dump(),
    }
    db_users.append(new_user)
    return new_user


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["OpenAI"],
    summary="OpenAI 채팅 요청",
    description="메시지를 OpenAI Responses API에 전달하고 생성된 답변을 반환합니다.",
    responses={
        502: {"description": "OpenAI API 호출 실패"},
        503: {"description": "OPENAI_API_KEY가 설정되지 않음"},
    },
)
async def chat(request: ChatRequest) -> ChatResponse:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("여기에_"):
        raise HTTPException(
            status_code=503,
            detail=".env 파일에 OPENAI_API_KEY를 설정해주세요.",
        )

    model = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")
    client = AsyncOpenAI(api_key=api_key)

    try:
        response = await client.responses.create(
            model=model,
            input=request.message,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="OpenAI API 호출에 실패했습니다.",
        ) from exc

    return ChatResponse(answer=response.output_text, model=model)


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["tags"] = [
        {"name": "시스템", "description": "서버 동작 및 상태 확인"},
        {"name": "사용자", "description": "Mock 사용자 조회 및 등록"},
        {"name": "OpenAI", "description": "OpenAI Responses API 연동"},
        {
            "name": "금리 예측",
            "description": "경제지표, 모델 검증 및 3개월 기준금리 방향 예측",
        },
    ]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
