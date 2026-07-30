# FastAPI Full Stack

상세 학습 노트: [WSL부터 FastAPI·Swagger·GitHub까지](docs/DEVELOPMENT_STACK_NOTES.md)

## 구조

```text
main.py        FastAPI 실행 진입점
backend/       FastAPI 백엔드
frontend/      HTML, CSS, JavaScript 프론트엔드
.env           로컬 API 키
```

## 실행

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn main:app --reload
```

서버 실행 후 아래 주소를 사용할 수 있습니다.

- 프론트엔드: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## 엔드포인트

- `GET /health`: 서버 상태 확인
- `GET /users`: 전체 사용자 조회
- `GET /users/{user_id}`: 사용자 단건 조회
- `POST /users`: 사용자 등록
- `POST /chat`: OpenAI Responses API 호출

`POST /chat` 요청 예시:

```json
{
  "message": "안녕! 한 문장으로 자기소개해줘."
}
```
