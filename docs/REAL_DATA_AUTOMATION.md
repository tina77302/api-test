# 실제 경제 데이터 자동 수집: 1단계

## 목표

한국은행 ECOS Open API 인증키를 사용해 금리 예측에 필요한 통계표와 세부 항목의
정확한 코드를 자동으로 찾는다.

통계 코드를 기억이나 블로그 예제에서 복사하지 않고 현재 ECOS 메타데이터에서
검색한 뒤 수집 설정으로 확정한다.

## 1. ECOS 인증키 발급

1. `https://ecos.bok.or.kr/api/` 접속
2. 회원가입 또는 로그인
3. 인증키 신청
4. 발급된 키 복사

인증키는 채팅, Python 코드, GitHub에 올리지 않는다.

## 2. `.env` 설정

프로젝트의 `.env` 파일:

```env
BOK_ECOS_API_KEY=발급받은_본인_키
```

`=` 주변에 공백을 넣지 않는다.

## 3. 통계표 탐색

```bash
source .venv/bin/activate
python -m data_pipeline.discover_ecos
```

다음 키워드에 해당하는 통계표와 세부 항목을 출력한다.

```text
기준금리
소비자물가
원/달러
실업률
국고채
```

출력에서 확인할 정보:

- 통계표 코드
- 통계표 이름
- 제공 주기
- 세부 항목 코드
- 데이터 시작·종료 시점

## 4. 다음 단계

탐색 결과로 확정한 코드를 이용해 실제 월별 데이터를 수집한다.

```bash
python -m data_pipeline.collect_ecos_data
```

```text
ECOS API 호출
    ↓
data/raw에 원본 응답 저장
    ↓
월별 단위 통일
    ↓
날짜 기준 병합
    ↓
3개월 후 목표값 생성
    ↓
data/processed에 학습 데이터 저장
```

생성되는 주요 파일:

```text
data/raw/ecos_current_rate.json
data/raw/ecos_cpi_index.json
data/raw/ecos_exchange_rate.json
data/raw/ecos_unemployment.json
data/raw/ecos_bond_3y.json
data/raw/fred_fedfunds.json
data/processed/monthly_interest_rate_data.csv
```

처리 과정:

1. 2000년 1월부터 현재까지 월별 자료를 조회한다.
2. 원본 ECOS 응답은 `data/raw`에 보관한다.
3. CPI 지수는 전년동월비 물가상승률로 변환한다.
4. 모든 지표가 존재하는 공통 월만 병합한다.
5. FRED `FEDFUNDS` 월별 미국 연방기금 실효금리를 병합한다.
6. 3개월 뒤 한국은행 기준금리를 목표값으로 만든다.

FRED API 사용 애플리케이션 고지:

> This product uses the FRED® API but is not endorsed or certified by the
> Federal Reserve Bank of St. Louis.

## 5. 실제 데이터 모델 비교

```bash
python -m ml.compare_real_models
```

처음 80% 기간으로 Linear Regression을 학습하고, 마지막 20% 기간을 테스트한다.
Baseline과 Linear Regression의 MAE와 방향 정확도를 같은 테스트 기간에서
비교한다.

## 6. 현재 월 잠정 데이터 수집과 시험 예측

현재 월의 일별 자료와 최신 확정 월 자료를 조합해 실시간 추론 입력을 만든다.

```bash
python -m data_pipeline.collect_live_features
```

생성 파일:

```text
data/live/latest_features.json
```

시험 예측:

```bash
python -m ml.predict_live
```

예측 결과 시각화:

```bash
python -m ml.visualize_live_prediction
```

생성 이미지:

```text
outputs/live_prediction_dashboard.png
```

예측 결과 파일:

```text
outputs/live_prediction.json
```

현재 월 데이터는 잠정값이므로 확정 학습 데이터에 추가하지 않는다. 환율,
국고채, 미국 금리는 월초부터 기준일까지의 평균을 사용하고 물가와 실업률은
이용 가능한 최신 확정 월을 사용한다.
