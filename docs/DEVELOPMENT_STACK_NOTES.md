# WSL부터 FastAPI·Swagger·GitHub까지 개발 환경 학습 노트

이 문서는 현재 `api-test` 프로젝트를 기준으로 다음 기술이 어떤 역할을 하고,
서로 어떻게 연결되는지 설명한다.

- WSL과 VM
- Visual Studio Code
- Python
- Python `venv` 가상환경
- FastAPI
- Uvicorn
- API와 HTTP
- OpenAPI와 Swagger
- Git과 GitHub

---

## 1. 전체 구조 한눈에 보기

```text
Windows
└── WSL 2 (Linux/Ubuntu 개발 환경)
    └── 프로젝트 폴더
        ├── VS Code로 파일 편집
        ├── Git으로 변경 이력 관리
        ├── .venv에 Python 패키지 격리
        ├── FastAPI로 백엔드 API 작성
        ├── Uvicorn으로 FastAPI 실행
        ├── Swagger UI로 API 확인·테스트
        └── GitHub에 Git 커밋 업로드

브라우저의 프론트엔드
    │
    │ HTTP 요청: GET /users, POST /chat 등
    ▼
Uvicorn
    ▼
FastAPI 백엔드
    ├── 사용자 데이터 처리
    └── OpenAI API 같은 외부 API 호출
```

각 도구는 경쟁 관계가 아니라 서로 다른 역할을 담당한다.

| 기술 | 한 문장 설명 |
|---|---|
| WSL | Windows 안에서 Linux 개발 환경을 사용하게 해준다. |
| VM | 하나의 컴퓨터 안에서 별도의 가상 컴퓨터를 실행한다. |
| VS Code | 코드를 작성하고 터미널·Git·디버깅을 함께 사용하는 편집기다. |
| Python | 현재 백엔드 코드를 작성한 프로그래밍 언어다. |
| `venv` | 프로젝트별 Python과 패키지 사용 환경을 분리한다. |
| FastAPI | Python으로 웹 API 서버를 만드는 프레임워크다. |
| Uvicorn | FastAPI 애플리케이션을 실제로 실행하고 HTTP 요청을 받는다. |
| API | 프로그램끼리 정해진 규칙으로 요청과 응답을 주고받는 접점이다. |
| OpenAPI | API 주소, 입력, 출력 등을 기술하는 표준 명세다. |
| Swagger UI | OpenAPI 명세를 사람이 보고 테스트할 수 있는 화면으로 만든다. |
| Git | 파일 변경 이력을 로컬에서 버전별로 저장한다. |
| GitHub | Git 저장소를 인터넷에서 보관하고 공유·협업하는 서비스다. |

---

## 2. WSL과 VM

### 2.1 WSL이란?

WSL은 **Windows Subsystem for Linux**의 약자다. Windows를 종료하거나
듀얼 부팅하지 않고 Ubuntu 같은 Linux 배포판과 Bash 명령을 사용할 수 있게 한다.

WSL 터미널에서는 다음과 같은 Linux 명령을 사용한다.

```bash
pwd
ls
cd
mkdir
python3
git
```

Windows PowerShell 명령과 WSL Bash 명령은 실행 환경이 다르다. 예를 들어:

```text
Windows 경로: C:\Users\사용자명\project
WSL 경로:     /home/사용자명/project
```

Windows 드라이브는 WSL에서 일반적으로 다음처럼 접근한다.

```text
C:\  →  /mnt/c/
D:\  →  /mnt/d/
```

### 2.2 WSL 1과 WSL 2

일반적인 개발 환경에서는 WSL 2를 많이 사용한다. WSL 2는 실제 Linux 커널을
사용하며 Linux 도구와의 호환성이 좋다.

PowerShell에서 설치 상태를 확인한다.

```powershell
wsl --list --verbose
```

예시:

```text
NAME      STATE    VERSION
Ubuntu    Running  2
```

WSL 설치 명령은 관리자 권한 PowerShell에서 실행한다.

```powershell
wsl --install
```

Microsoft 공식 문서에 따르면 이 명령은 필요한 Windows 기능과 기본 Ubuntu
배포판을 설치하며, 설치 후 재부팅이 필요할 수 있다.

### 2.3 WSL과 일반 VM의 차이

| 구분 | WSL 2 | 일반 VM |
|---|---|---|
| 목적 | Windows에서 Linux 개발 도구 사용 | 완전히 분리된 운영체제 실행 |
| Windows 통합 | 높음 | 상대적으로 낮음 |
| 시작 속도 | 빠른 편 | 부팅 과정이 더 뚜렷함 |
| 자원 관리 | Windows와 동적으로 공유 | CPU·메모리를 명시적으로 할당하는 경우가 많음 |
| 파일 접근 | Windows와 Linux 파일 접근이 편리함 | 공유 폴더나 네트워크 설정이 필요할 수 있음 |
| 격리 수준 | 개발 편의 중심 | 독립 서버 실습과 강한 분리에 유리 |

WSL 2 내부에서도 가상화 기술이 사용되지만, 사용 경험과 목적은 VirtualBox,
VMware 등에 별도의 전체 운영체제를 설치하는 전통적인 VM과 다르다.

### 2.4 프로젝트 파일은 어디에 둘까?

Linux 도구를 중심으로 개발한다면 프로젝트를 WSL의 Linux 파일 시스템에 두는
편이 일반적으로 편리하다.

```text
/home/사용자명/projects/api-test
```

현재 환경의 프로젝트 경로 예시는 다음과 같다.

```text
/root/ai-quant-preparation/api-test
```

`/mnt/c/...`에 놓인 프로젝트도 편집할 수 있지만, 파일 감시나 대량 파일 작업의
동작 차이를 겪을 수 있다.

공식 참고:

- [WSL 설치](https://learn.microsoft.com/windows/wsl/install)
- [WSL 개발 환경 설정](https://learn.microsoft.com/windows/wsl/setup/environment)
- [WSL 버전 비교](https://learn.microsoft.com/windows/wsl/compare-versions)

---

## 3. Visual Studio Code와 WSL

### 3.1 VS Code의 역할

VS Code는 단순 메모장이 아니라 다음 기능을 한 화면에서 제공한다.

- 프로젝트 파일 탐색
- Python 코드 작성과 자동완성
- 내장 터미널
- 오류 표시
- 디버깅
- Git 변경사항 확인
- 확장 프로그램 설치
- 파일 아이콘과 색상 테마

### 3.2 Windows VS Code와 WSL 연결

VS Code 프로그램 자체는 Windows에 설치하고, **WSL 확장**을 이용해 WSL 내부
프로젝트를 여는 방식이 권장된다.

WSL 터미널에서 프로젝트 폴더로 이동한 후:

```bash
cd /root/ai-quant-preparation/api-test
code .
```

마지막의 점(`.`)은 **현재 폴더를 VS Code로 열라**는 의미다.

이 방식에서는:

- VS Code 화면은 Windows에서 실행된다.
- 프로젝트 파일, Python, Git, 터미널은 WSL 쪽에서 동작한다.
- VS Code 왼쪽 아래에 WSL 연결 상태가 표시된다.

### 3.3 확장 프로그램 설치 위치

테마처럼 화면만 바꾸는 확장은 Windows 쪽 설치만으로 충분한 경우가 많다.
Python 분석·디버깅처럼 코드를 실행하는 확장은 WSL 환경에도 설치해야 할 수 있다.

추천 확장:

- WSL
- Python
- Pylance
- 선택 사항: 파일 아이콘 테마

### 3.4 Python 인터프리터 선택

VS Code가 프로젝트의 `.venv`를 사용하도록 설정한다.

1. `Ctrl + Shift + P`
2. `Python: Select Interpreter`
3. 프로젝트의 `.venv/bin/python` 선택

현재 프로젝트에서는 다음 경로다.

```text
/root/ai-quant-preparation/api-test/.venv/bin/python
```

오른쪽 아래 또는 상태 표시줄에서 선택된 Python 환경을 확인할 수 있다.

공식 참고:

- [VS Code에서 WSL 사용하기](https://learn.microsoft.com/windows/wsl/tutorials/wsl-vscode)

---

## 4. Python과 `venv` 가상환경

### 4.1 Python의 역할

Python은 프로그래밍 언어이며, 현재 프로젝트의 FastAPI 백엔드는 Python으로
작성되어 있다.

버전 확인:

```bash
python3 --version
```

`python`과 `python3`가 서로 다른 실행 파일을 가리키는 환경도 있으므로 경로까지
확인하면 도움이 된다.

```bash
which python
which python3
```

### 4.2 가상환경이 필요한 이유

프로젝트 A는 FastAPI의 한 버전을 사용하고 프로젝트 B는 다른 버전을 사용할 수
있다. 모든 패키지를 시스템 Python에 설치하면 버전 충돌이 생길 수 있다.

`venv`는 프로젝트별로 다음을 격리한다.

- Python 실행 경로
- `pip`로 설치한 패키지
- 패키지 버전

```text
프로젝트 A/.venv → FastAPI 버전 A
프로젝트 B/.venv → FastAPI 버전 B
```

가상환경은 Docker나 VM처럼 운영체제를 가상화하지 않는다. Python 실행 환경과
패키지를 가볍게 분리하는 도구다.

### 4.3 가상환경 생성과 활성화

WSL/Linux에서 생성:

```bash
python3 -m venv .venv
```

활성화:

```bash
source .venv/bin/activate
```

활성화 후 프롬프트 예시:

```text
(.venv) user@computer:~/project$
```

활성화 여부 확인:

```bash
which python
python --version
python -m pip --version
```

출력 경로가 프로젝트의 `.venv` 안을 가리켜야 한다.

비활성화:

```bash
deactivate
```

### 4.4 Windows와 WSL 가상환경 경로 차이

WSL/Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```bat
.venv\Scripts\activate.bat
```

WSL에서 만든 `.venv`를 Windows Python용으로 재사용하거나, 반대로 Windows에서
만든 `.venv`를 WSL Python용으로 재사용하지 않는 것이 좋다. 운영체제에 따라
실행 파일과 일부 패키지 형식이 다르기 때문이다.

### 4.5 패키지 설치와 재현

현재 프로젝트 의존성 설치:

```bash
python -m pip install -r backend/requirements.txt
```

`requirements.txt`는 다른 사람이 같은 패키지를 설치할 수 있도록 패키지와
버전을 기록한 파일이다.

`.venv` 자체는 GitHub에 올리지 않는다.

```gitignore
.venv/
```

이유:

- 용량이 크다.
- 운영체제마다 내용이 달라질 수 있다.
- `requirements.txt`로 다시 만들 수 있다.

공식 참고:

- [Python venv 문서](https://docs.python.org/3/library/venv.html)

---

## 5. FastAPI

### 5.1 FastAPI란?

FastAPI는 Python으로 API 백엔드를 만드는 웹 프레임워크다.

FastAPI가 담당하는 대표 기능:

- URL과 Python 함수 연결
- 요청 데이터 읽기
- Pydantic을 통한 입력 검증
- Python 객체를 JSON 응답으로 변환
- HTTP 오류 응답 생성
- OpenAPI 명세 자동 생성
- Swagger UI와 ReDoc 제공

### 5.2 가장 작은 FastAPI 코드

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}
```

구성 요소:

```python
app = FastAPI()
```

FastAPI 애플리케이션 객체를 만든다.

```python
@app.get("/")
```

HTTP `GET /` 요청을 아래 함수에 연결하는 데코레이터다.

```python
async def root():
```

요청이 들어왔을 때 실행되는 함수다.

```python
return {"message": "Hello World"}
```

Python 딕셔너리를 반환하면 FastAPI가 JSON 응답으로 변환한다.

### 5.3 현재 프로젝트 구조

```text
backend/
├── __init__.py
├── main.py
└── requirements.txt
```

현재 FastAPI 객체의 import 경로는 다음과 같다.

```text
backend.main:app
│       │    └── main.py 안의 app 변수
│       └─────── main.py 모듈
└─────────────── backend 패키지
```

### 5.4 Pydantic 데이터 모델

```python
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    age: int | None = None
```

요청 JSON:

```json
{
  "username": "honggildong",
  "email": "hong@example.com",
  "age": 25
}
```

FastAPI와 Pydantic은 다음을 자동으로 처리한다.

- 필수 필드 확인
- 데이터 타입 확인
- 설정된 최소·최대 길이 확인
- 잘못된 요청에 `422 Unprocessable Entity` 응답
- OpenAPI 요청 스키마 생성

### 5.5 경로 파라미터와 요청 본문

경로 파라미터:

```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    ...
```

요청:

```http
GET /users/3
```

여기서 `3`은 `user_id`에 들어간다.

요청 본문:

```python
@app.post("/users")
async def create_user(user: UserCreate):
    ...
```

요청:

```http
POST /users
Content-Type: application/json

{
  "username": "honggildong",
  "email": "hong@example.com",
  "age": 25
}
```

### 5.6 예외와 상태 코드

```python
from fastapi import HTTPException

raise HTTPException(
    status_code=404,
    detail="사용자를 찾을 수 없습니다.",
)
```

응답:

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "detail": "사용자를 찾을 수 없습니다."
}
```

### 5.7 Mock 데이터의 한계

현재 `db_users`는 Python 메모리에 들어 있는 리스트다.

```python
db_users = generate_mock_users()
```

장점:

- 데이터베이스 설치 없이 빠르게 API 연습 가능
- 서버 동작과 프론트엔드 연결 확인에 적합

한계:

- 서버 재시작 시 데이터 초기화
- 여러 서버 프로세스가 같은 데이터를 공유하지 못함
- 실제 운영 서비스에 적합하지 않음

실제 서비스에서는 PostgreSQL, MySQL, SQLite 같은 데이터베이스와 SQLAlchemy
등을 연결하는 방식을 고려한다.

공식 참고:

- [FastAPI 첫 단계](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI 요청 본문](https://fastapi.tiangolo.com/tutorial/body/)

---

## 6. Uvicorn

### 6.1 Uvicorn의 역할

FastAPI는 API의 규칙과 처리 로직을 만든다. 하지만 FastAPI 코드만 작성했다고
컴퓨터가 자동으로 포트에서 요청을 받는 것은 아니다.

Uvicorn은 **ASGI 서버**로서 다음을 담당한다.

- 지정한 IP와 포트에서 대기
- 브라우저나 프론트엔드의 HTTP 요청 수신
- 요청을 FastAPI 애플리케이션에 전달
- FastAPI가 만든 응답을 클라이언트에 전송

```text
클라이언트 → Uvicorn → FastAPI 함수
클라이언트 ← Uvicorn ← FastAPI 응답
```

### 6.2 현재 프로젝트 실행 명령

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```

명령 해석:

| 부분 | 의미 |
|---|---|
| `uvicorn` | Uvicorn 서버 실행 |
| `backend.main` | `backend/main.py` 모듈 |
| `:app` | 모듈 안의 `app = FastAPI(...)` 객체 |
| `--reload` | Python 파일 변경 시 개발 서버 자동 재시작 |

기본 주소:

```text
http://127.0.0.1:8000
```

`127.0.0.1`은 현재 컴퓨터 자신을 의미하는 loopback 주소이고, `8000`은 포트다.

### 6.3 주요 실행 옵션

```bash
uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
```

- `--host 127.0.0.1`: 현재 컴퓨터에서만 접근
- `--host 0.0.0.0`: 사용 가능한 모든 네트워크 인터페이스에서 접근
- `--port 8000`: 8000번 포트 사용
- `--reload`: 개발 중 자동 재시작

`0.0.0.0`은 브라우저에 입력하는 접속 주소가 아니라 서버의 바인딩 범위다.
같은 컴퓨터에서는 `http://127.0.0.1:8000`으로 접속한다.

`--reload`는 개발 편의를 위한 옵션이다. 운영 환경에서는 보통 사용하지 않는다.
Uvicorn 공식 문서상 `--reload`와 여러 worker를 지정하는 `--workers`는 동시에
사용할 수 없다.

공식 참고:

- [Uvicorn 설정](https://www.uvicorn.org/settings/)

---

## 7. API와 HTTP

### 7.1 API란?

API는 **Application Programming Interface**의 약자다. 프로그램이 다른
프로그램의 기능이나 데이터에 접근하기 위한 규칙과 접점이다.

식당에 비유하면:

```text
손님            메뉴판/API 명세        주방/백엔드
요청 작성   →   주문 규칙 확인    →   요청 처리
응답 받음   ←   응답 형식         ←   결과 생성
```

현재 프로젝트에서는 프론트엔드 JavaScript가 FastAPI에 HTTP 요청을 보낸다.

```javascript
const response = await fetch("/users");
const users = await response.json();
```

### 7.2 엔드포인트

엔드포인트는 API를 호출하는 구체적인 주소와 HTTP 메서드 조합이다.

```text
GET  /users
POST /users
POST /chat
```

`GET /users`와 `POST /users`는 경로는 같지만 메서드가 다르므로 서로 다른
작업이다.

### 7.3 HTTP 메서드

| 메서드 | 일반적인 의미 | 예시 |
|---|---|---|
| `GET` | 데이터 조회 | `GET /users` |
| `POST` | 새 데이터 생성 또는 작업 요청 | `POST /users` |
| `PUT` | 리소스 전체 수정 | `PUT /users/1` |
| `PATCH` | 리소스 일부 수정 | `PATCH /users/1` |
| `DELETE` | 데이터 삭제 | `DELETE /users/1` |

이 의미는 널리 쓰이는 관례이며, 서버 코드가 실제 동작을 결정한다.

### 7.4 요청의 구성

HTTP 요청에는 다음이 포함될 수 있다.

```text
메서드: POST
경로: /users
헤더: Content-Type: application/json
본문: {"username": "kim", "email": "kim@example.com"}
```

주요 입력 위치:

- Path parameter: `/users/3`의 `3`
- Query parameter: `/users?limit=10`의 `limit=10`
- Header: 인증 토큰, 콘텐츠 형식 등
- Body: JSON으로 보내는 주요 데이터

### 7.5 응답의 구성

```text
상태 코드: 201
헤더: Content-Type: application/json
본문: {"id": 31, "username": "kim", ...}
```

자주 보는 상태 코드:

| 코드 | 의미 |
|---|---|
| `200 OK` | 요청 성공 |
| `201 Created` | 새 데이터 생성 성공 |
| `204 No Content` | 성공했지만 응답 본문 없음 |
| `400 Bad Request` | 잘못된 요청 |
| `401 Unauthorized` | 인증 필요 또는 인증 실패 |
| `403 Forbidden` | 인증됐지만 권한 없음 |
| `404 Not Found` | 대상 없음 |
| `422 Unprocessable Entity` | 입력 형식이나 검증 실패 |
| `500 Internal Server Error` | 서버 내부 오류 |
| `502 Bad Gateway` | 서버가 호출한 외부 서비스에서 문제 발생 |
| `503 Service Unavailable` | 현재 서비스를 처리할 준비가 안 됨 |

### 7.6 JSON

JSON은 프론트엔드와 백엔드가 데이터를 주고받을 때 흔히 사용하는 텍스트 형식이다.

```json
{
  "id": 1,
  "username": "user1",
  "email": "user1@example.com",
  "age": 25
}
```

JSON과 Python 자료형의 대표 대응:

| JSON | Python |
|---|---|
| object | `dict` |
| array | `list` |
| string | `str` |
| number | `int`, `float` |
| boolean | `bool` |
| null | `None` |

### 7.7 외부 API와 API 키

현재 `/chat` 엔드포인트는 FastAPI 서버가 OpenAI API를 다시 호출하는 구조다.

```text
브라우저
  → 우리 FastAPI의 POST /chat
    → OpenAI API
    ← OpenAI 답변
  ← 브라우저에 답변 반환
```

OpenAI API 키는 브라우저 JavaScript에 넣지 않는다. 브라우저에 넣으면 방문자가
개발자 도구나 네트워크 요청에서 키를 확인할 수 있기 때문이다.

안전한 구조:

```text
frontend/app.js             키 없음
backend/main.py             환경변수 이름만 사용
.env                        실제 키 저장, Git 제외
.env.example                예시 값만 저장, Git 포함 가능
```

`.env`:

```env
OPENAI_API_KEY=실제_키
OPENAI_MODEL=gpt-5.6-terra
```

`.gitignore`:

```gitignore
.env
```

키가 공개 저장소나 채팅에 노출되면 해당 키를 폐기하고 새로 발급해야 한다.

### 7.8 CORS

CORS는 브라우저가 서로 다른 출처(origin) 사이의 요청을 제한하는 보안 규칙과
관련된다.

다음은 서로 다른 출처다.

```text
http://localhost:3000
http://localhost:8000
```

포트가 다르기 때문이다.

현재 프로젝트는 FastAPI가 프론트엔드를 같은 `8000` 포트에서 함께 제공하므로
기본 사용에서는 같은 출처가 된다. 프론트엔드를 별도 개발 서버에서 실행할 경우
FastAPI의 `CORSMiddleware`에 허용할 출처를 명시해야 한다.

운영 환경에서 `allow_origins=["*"]`를 무조건 사용하는 것보다 실제 프론트엔드
도메인을 구체적으로 지정하는 것이 좋다.

---

## 8. OpenAPI와 Swagger

### 8.1 OpenAPI와 Swagger는 같은 것인가?

완전히 같은 말은 아니다.

- **OpenAPI Specification**: REST API를 기술하는 표준 형식
- **Swagger**: OpenAPI를 작성·표시·활용하는 도구 모음
- **Swagger UI**: OpenAPI 문서를 대화형 웹 화면으로 렌더링하는 도구

역사적으로 Swagger Specification이라 불리던 명세가 OpenAPI Specification으로
이름이 바뀌었다. 현재는 표준을 OpenAPI, 관련 도구를 Swagger라고 구분하면 된다.

### 8.2 FastAPI에서 자동 문서가 만들어지는 과정

```text
Python 타입과 Pydantic 모델
        +
FastAPI 경로 데코레이터
        ▼
OpenAPI JSON 자동 생성
        ▼
Swagger UI / ReDoc이 화면으로 표시
```

현재 프로젝트 주소:

```text
Swagger UI:  http://127.0.0.1:8000/docs
ReDoc:       http://127.0.0.1:8000/redoc
OpenAPI JSON:http://127.0.0.1:8000/openapi.json
```

### 8.3 Swagger UI의 역할

Swagger UI에서는:

- 전체 엔드포인트 목록 확인
- 요청 파라미터와 JSON 구조 확인
- 가능한 응답 코드 확인
- `Try it out`으로 실제 요청 전송
- 응답 상태, 헤더, 본문 확인

Swagger UI는 최종 사용자를 위한 실제 프론트엔드가 아니다. 개발자와 API
사용자를 위한 **대화형 API 명세 및 테스트 화면**이다.

### 8.4 FastAPI 코드가 명세에 반영되는 예

```python
@app.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
    tags=["사용자"],
    summary="사용자 등록",
    description="새로운 사용자를 등록합니다.",
)
async def create_user(user: UserCreate):
    ...
```

Swagger에 반영되는 정보:

- 메서드: `POST`
- 경로: `/users`
- 태그: `사용자`
- 제목: `사용자 등록`
- 설명
- 요청 모델: `UserCreate`
- 성공 응답 모델: `UserResponse`
- 성공 상태 코드: `201`

### 8.5 API 명세가 중요한 이유

- 프론트엔드 개발자가 요청 형식을 알 수 있다.
- 백엔드 개발자가 API 계약을 명확히 만들 수 있다.
- QA가 테스트할 엔드포인트와 응답을 확인할 수 있다.
- 자동 클라이언트 코드 생성에 활용할 수 있다.
- 사람과 프로그램이 같은 명세를 읽을 수 있다.

공식 참고:

- [FastAPI 자동 API 문서](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI 문서 URL 설정](https://fastapi.tiangolo.com/tutorial/metadata/)
- [OpenAPI와 Swagger 소개](https://swagger.io/docs/specification/v3_0/about/)

---

## 9. Git

### 9.1 Git이란?

Git은 파일 변경 이력을 관리하는 **분산 버전 관리 시스템**이다.

Git으로 할 수 있는 일:

- 특정 시점의 프로젝트 상태 저장
- 누가 무엇을 변경했는지 확인
- 이전 변경사항 비교
- 브랜치에서 새 기능 개발
- 충돌을 해결하며 여러 사람과 협업

Git은 인터넷이 없어도 로컬 커밋을 만들 수 있다.

### 9.2 Git의 세 영역

```text
Working Directory       Staging Area          Repository
현재 수정 중인 파일  →  다음 커밋 후보 파일  →  커밋된 이력
                    git add               git commit
```

1. Working directory: 실제로 편집 중인 파일
2. Staging area: 다음 커밋에 포함하기로 선택한 파일
3. Local repository: 커밋으로 저장된 이력

### 9.3 기본 작업 흐름

현재 상태 확인:

```bash
git status
```

변경 내용 확인:

```bash
git diff
```

파일을 staging area에 추가:

```bash
git add backend/main.py
git add frontend/
```

커밋:

```bash
git commit -m "Add user API and frontend"
```

GitHub에 업로드:

```bash
git push origin main
```

### 9.4 자주 사용하는 명령

| 명령 | 의미 |
|---|---|
| `git status` | 변경·추적 상태 확인 |
| `git diff` | 아직 staging하지 않은 변경 확인 |
| `git diff --cached` | staging된 변경 확인 |
| `git add <파일>` | 커밋 후보로 추가 |
| `git commit -m "메시지"` | 로컬 이력 저장 |
| `git log --oneline` | 커밋 목록 확인 |
| `git branch` | 브랜치 확인 |
| `git switch <브랜치>` | 브랜치 이동 |
| `git pull` | 원격 변경을 가져와 현재 브랜치에 반영 |
| `git push` | 로컬 커밋을 원격에 업로드 |
| `git remote -v` | 연결된 원격 저장소 주소 확인 |

### 9.5 `.gitignore`

Git으로 추적하지 않을 파일과 폴더를 지정한다.

현재 프로젝트에서 중요한 예:

```gitignore
.env
.venv/
__pycache__/
```

- `.env`: 비밀키가 들어갈 수 있음
- `.venv`: 다시 설치할 수 있고 용량이 큼
- `__pycache__`: Python이 자동 생성하는 캐시

`.gitignore`에 추가하기 전에 이미 Git이 추적하던 파일은 자동으로 추적 해제되지
않는다. 특히 비밀키는 커밋 전에 `git status`와 staged diff를 확인해야 한다.

---

## 10. GitHub

### 10.1 Git과 GitHub의 차이

| Git | GitHub |
|---|---|
| 버전 관리 프로그램 | Git 저장소 호스팅 서비스 |
| 로컬에서 동작 가능 | 인터넷의 원격 저장소 |
| 커밋·브랜치 관리 | 공유·협업·리뷰·이슈·Actions 등 |
| `git commit` | `git push`로 커밋 수신 |

비유:

```text
Git 커밋 = 내 컴퓨터에 저장한 작업 일지
GitHub    = 작업 일지를 백업·공유하는 온라인 공간
```

### 10.2 로컬 저장소와 원격 저장소

현재 원격 이름은 일반적으로 `origin`이다.

```bash
git remote -v
```

예시:

```text
origin  https://github.com/사용자명/api-test.git (fetch)
origin  https://github.com/사용자명/api-test.git (push)
```

- `fetch`: GitHub에서 이력을 가져오는 주소
- `push`: GitHub로 이력을 올리는 주소

### 10.3 GitHub에 올리는 순서

```bash
git status
git diff
git add README.md backend frontend
git diff --cached
git commit -m "Describe the change"
git push origin main
```

중요한 구분:

- `git add`: 아직 저장이 아니라 커밋 후보 선택
- `git commit`: 로컬 Git에 저장
- `git push`: GitHub에 업로드

커밋만 하고 push하지 않으면 GitHub에는 나타나지 않는다.

### 10.4 Clone, Pull, Push

```text
git clone: 원격 저장소를 처음 통째로 복제
git pull:  원격의 새로운 변경을 현재 로컬 브랜치에 반영
git push:  로컬의 새로운 커밋을 원격으로 전송
```

### 10.5 브랜치와 Pull Request

`main`은 보통 안정적인 기본 브랜치로 사용한다. 협업에서는 새 기능을 별도
브랜치에 작성한 후 Pull Request로 검토하고 `main`에 합친다.

```bash
git switch -c feature/login
# 코드 수정
git add .
git commit -m "Add login API"
git push -u origin feature/login
```

그 후 GitHub에서 Pull Request를 생성하고 리뷰 후 병합한다.

### 10.6 GitHub에 올리면 안 되는 것

- 실제 API 키
- 비밀번호
- 인증서 개인키
- 데이터베이스 접속 비밀값
- 사용자 개인정보
- `.env`

비밀값이 한번이라도 공개 저장소에 push되었다면 파일만 삭제하는 것으로 충분하지
않을 수 있다. Git 이력에 남을 수 있으므로 먼저 해당 키를 폐기·교체해야 한다.

공식 참고:

- [Git 시작하기](https://docs.github.com/get-started/learning-to-code/getting-started-with-git)
- [Git과 GitHub 기본 개념](https://docs.github.com/get-started/using-git/about-git)
- [원격 저장소](https://docs.github.com/get-started/git-basics/about-remote-repositories)

---

## 11. 현재 프로젝트 실행 전체 순서

### 11.1 WSL 터미널 열기

Windows Terminal 또는 VS Code의 WSL 터미널을 연다.

### 11.2 프로젝트 폴더 이동

```bash
cd /root/ai-quant-preparation/api-test
```

현재 위치 확인:

```bash
pwd
```

### 11.3 VS Code 열기

```bash
code .
```

### 11.4 가상환경 활성화

```bash
source .venv/bin/activate
```

### 11.5 패키지 설치

처음 실행하거나 `requirements.txt`가 변경된 경우:

```bash
python -m pip install -r backend/requirements.txt
```

### 11.6 환경변수 설정

`.env`:

```env
OPENAI_API_KEY=본인의_실제_API_키
OPENAI_MODEL=gpt-5.6-terra
```

키를 채팅, 소스 코드, GitHub에 올리지 않는다.

### 11.7 서버 실행

```bash
uvicorn backend.main:app --reload
```

### 11.8 브라우저 확인

```text
프론트엔드: http://127.0.0.1:8000
Swagger:    http://127.0.0.1:8000/docs
ReDoc:      http://127.0.0.1:8000/redoc
OpenAPI:    http://127.0.0.1:8000/openapi.json
```

### 11.9 서버 종료

서버를 실행한 터미널에서:

```text
Ctrl + C
```

### 11.10 Git 저장과 GitHub 업데이트

```bash
git status
git diff
git add README.md backend frontend docs
git commit -m "Update project"
git push origin main
```

---

## 12. 자주 발생하는 문제

### 문제 1: `command not found: uvicorn`

원인:

- 가상환경을 활성화하지 않음
- Uvicorn이 해당 가상환경에 설치되지 않음

확인 및 해결:

```bash
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

`python -m uvicorn` 방식은 현재 선택한 Python에 설치된 Uvicorn을 명확하게
실행한다.

### 문제 2: `Could not import module`

원인:

- 실행 위치가 잘못됨
- `backend.main:app` 경로 오타
- Python 문법 또는 import 오류

프로젝트 루트에서 실행한다.

```bash
cd /root/ai-quant-preparation/api-test
uvicorn backend.main:app --reload
```

### 문제 3: 8000번 포트가 이미 사용 중

다른 포트로 실행:

```bash
uvicorn backend.main:app --reload --port 8001
```

접속:

```text
http://127.0.0.1:8001
```

### 문제 4: Swagger는 열리지만 `/chat`이 503

`.env`에 실제 `OPENAI_API_KEY`가 설정되지 않은 상태다.

`.env` 파일 이름, 변수 이름, 키 값을 확인한 뒤 서버를 재시작한다.

```env
OPENAI_API_KEY=실제_키
```

### 문제 5: 프론트엔드에서 API 요청 실패

확인 순서:

1. Uvicorn이 실행 중인지 확인
2. 브라우저 개발자 도구의 Network 탭 확인
3. 요청 URL과 HTTP 메서드 확인
4. 응답 상태 코드 확인
5. 서로 다른 포트라면 CORS 설정 확인
6. Uvicorn 터미널의 오류 로그 확인

### 문제 6: VS Code가 다른 Python을 사용

```bash
which python
```

VS Code에서:

1. `Ctrl + Shift + P`
2. `Python: Select Interpreter`
3. `.venv/bin/python` 선택

### 문제 7: 수정했는데 GitHub에 안 보임

```bash
git status
git log -1 --oneline
git status --branch
```

커밋만 있고 push하지 않았을 수 있다.

```bash
git push origin main
```

### 문제 8: `.env`가 Git에 포함될까 걱정됨

```bash
git check-ignore -v .env
git status --ignored
```

`.env`가 ignored로 표시되어야 한다. 키 전체를 터미널에 출력해 확인하지 않는다.

---

## 13. 핵심 용어 복습

| 용어 | 뜻 |
|---|---|
| 개발 환경 | 코드를 작성·실행·검사하는 도구와 설정의 조합 |
| 런타임 | 프로그램이 실제로 실행되는 환경 |
| 프레임워크 | 애플리케이션 구조와 공통 기능을 제공하는 기반 |
| 라이브러리 | 코드에서 불러와 사용하는 기능 모음 |
| 서버 | 요청을 기다렸다가 응답하는 프로그램 또는 컴퓨터 |
| 클라이언트 | 서버에 요청하는 프로그램 |
| 백엔드 | 데이터 처리, 비즈니스 로직, DB·외부 API 연결 담당 |
| 프론트엔드 | 사용자가 보고 조작하는 화면 담당 |
| 라우트/엔드포인트 | 메서드와 URL로 구분되는 API 접점 |
| 포트 | 한 컴퓨터 안에서 네트워크 프로그램을 구분하는 번호 |
| 환경변수 | 코드 밖에서 프로그램 설정과 비밀값을 전달하는 값 |
| 의존성 | 프로젝트가 실행되기 위해 필요한 외부 패키지 |
| 스키마 | 데이터 또는 API 구조에 대한 설명 |
| 직렬화 | Python 객체 등을 JSON 같은 전송 형식으로 바꾸는 과정 |
| 역직렬화 | JSON 등을 프로그램의 객체로 바꾸는 과정 |
| 인증 | 사용자가 누구인지 확인 |
| 인가 | 인증된 사용자가 무엇을 할 수 있는지 확인 |
| 커밋 | Git에 저장한 프로젝트 상태의 스냅샷 |
| 브랜치 | 독립적으로 변경을 진행하는 Git 이력의 갈래 |
| 원격 저장소 | GitHub 등에 있는 네트워크상의 Git 저장소 |

---

## 14. 가장 중요한 구분

```text
WSL       ≠ Python 가상환경
WSL       ≠ 일반적인 독립 VM
FastAPI   ≠ Uvicorn
OpenAPI   ≠ Swagger UI
Swagger   ≠ 실제 서비스 프론트엔드
Git       ≠ GitHub
git commit ≠ git push
.env      ≠ .env.example
백엔드 API ≠ 외부 OpenAI API
```

- WSL은 Linux 개발 환경이다.
- `venv`는 Python 패키지 환경이다.
- FastAPI는 API 로직을 만든다.
- Uvicorn은 FastAPI 앱을 실행한다.
- OpenAPI는 명세 표준이다.
- Swagger UI는 그 명세를 보여주고 테스트하게 한다.
- Git은 버전 관리 도구다.
- GitHub는 Git 저장소를 호스팅한다.
- `.env`에는 실제 비밀값, `.env.example`에는 예시만 둔다.
