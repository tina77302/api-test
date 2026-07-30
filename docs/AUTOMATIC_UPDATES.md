# 기준금리 예측 플랫폼 자동 업데이트

## 한 번에 전체 업데이트

프로젝트 폴더에서 다음을 실행한다.

```bash
source .venv/bin/activate
python -m automation.update_forecast
```

이 명령은 다음 작업을 순서대로 실행한다.

```text
ECOS·FRED 확정 월 데이터 수집
현재 월 잠정 데이터 수집
회귀 모델 비교와 최신 예측
포스트 팬데믹 모델 예측
TimeSeriesSplit 모델 튜닝
대시보드 이미지 생성
업데이트 상태 기록
```

동시에 두 업데이트가 실행되지 않도록 잠금 파일을 사용한다. 실행 상태는
`outputs/update_status.json`과 `GET /forecast/status`에서 확인할 수 있다.

## 터미널을 켜둔 상태에서 매일 업데이트

```bash
python -m automation.run_scheduler --hours 24
```

실행 직후 한 번 업데이트하고 이후 24시간마다 반복한다. 터미널을 닫거나
WSL을 종료하면 스케줄러도 멈춘다.

## WSL cron으로 매일 오전 9시 업데이트

가상환경 Python과 프로젝트의 절대경로를 사용한다.

```bash
crontab -e
```

다음 한 줄을 추가한다.

```cron
0 9 * * * cd /root/ai-quant-preparation/api-test && /root/ai-quant-preparation/api-test/.venv/bin/python -m automation.update_forecast >> /root/ai-quant-preparation/api-test/outputs/update.log 2>&1
```

WSL 배포판이 실행 중이고 cron 서비스가 작동할 때만 실행된다. Windows가
꺼져 있거나 WSL이 완전히 중지돼 있으면 예약 작업도 실행되지 않는다.
항상 실행해야 한다면 Windows 작업 스케줄러에서 WSL 명령을 호출하거나,
서버에 배포한 뒤 서버의 cron을 사용하는 편이 안정적이다.

## 웹 플랫폼 실행

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

- 대시보드: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- 최신 예측 API: `GET /forecast/latest`
- 최근 지표 API: `GET /forecast/history`
- 업데이트 상태 API: `GET /forecast/status`

API 키는 `.env`에만 저장하고 GitHub에 올리지 않는다.
