# RateScope 무료 공개 배포

목표 주소:

```text
https://ai-ratescope.onrender.com
```

실제 주소는 Render에서 같은 서비스 이름이 이미 사용 중이면 뒤에 임의 문자가
붙을 수 있다.

## 1. GitHub 비밀키 등록

GitHub 저장소에서 다음 메뉴로 이동한다.

```text
Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

다음 두 개를 등록한다.

```text
BOK_ECOS_API_KEY
FRED_API_KEY
```

값에는 로컬 `.env`에 저장한 각각의 키를 넣는다. 키를 코드나 workflow 파일에
직접 적으면 안 된다.

## 2. GitHub Actions 권한 확인

저장소에서 다음 메뉴로 이동한다.

```text
Settings
→ Actions
→ General
→ Workflow permissions
→ Read and write permissions
→ Save
```

`.github/workflows/update-forecast.yml`은 매일 한국시간 오전 9시 15분에
데이터와 모델 결과를 갱신하고 변경된 결과를 GitHub에 커밋한다. Actions
화면의 `Run workflow` 버튼으로 즉시 시험할 수도 있다.

## 3. Render 무료 웹서비스 생성

1. Render에 GitHub 계정으로 가입한다.
2. `New +` → `Blueprint`를 선택한다.
3. 비공개 `api-test` 저장소 접근을 허용한다.
4. 저장소의 `render.yaml`을 확인하고 배포한다.
5. 환경변수 입력 화면에서 ECOS·FRED 키를 등록한다.
6. OpenAI 채팅 기능을 사용할 경우에만 `OPENAI_API_KEY`를 추가한다.

Render는 다음 설정을 자동으로 읽는다.

```text
서비스: ai-ratescope
플랜: Free
빌드: pip install -r backend/requirements-web.txt
실행: uvicorn main:app --host 0.0.0.0 --port $PORT
상태 확인: /health
```

## 4. 동작 구조

```text
GitHub Actions — 매일 데이터와 예측 결과 갱신
        ↓ 새 커밋
Render — GitHub 변경 감지 후 자동 재배포
        ↓
무료 onrender.com 주소에서 최신 결과 제공
```

무료 서비스는 일정 시간 요청이 없을 때 절전될 수 있어 첫 접속이 느릴 수
있다. 로컬의 `automation.run_scheduler`는 Render에서 실행하지 않는다.

## 보안

- `.env`는 GitHub에 업로드하지 않는다.
- API 키는 GitHub Actions Secrets와 Render Environment에만 등록한다.
- `/forecast` API는 읽기 전용이며 자동 업데이트를 직접 실행하지 않는다.
