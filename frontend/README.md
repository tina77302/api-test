# Frontend structure

RateScope는 별도 빌드 도구 없이 FastAPI가 정적 HTML, CSS, JavaScript를 제공합니다.

```text
pages/                         URL별 HTML 문서
assets/css/                    공통 디자인 시스템과 반응형 스타일
assets/data/                   화면에서 읽는 정적 도메인 데이터
assets/js/core/                전 페이지 공통 동작
assets/js/pages/               페이지별 화면과 데이터 렌더링
assets/js/components/          독립적으로 재사용 가능한 UI 기능
```

## Ownership

- `pages/index.html` + `assets/js/pages/home.js`: 현재 전망 요약
- `pages/learn.html` + `assets/js/pages/learn.js`: Learn Center
- `pages/model.html` + `assets/js/pages/model.js`: 모델·차트·검증 화면
- `assets/js/components/prediction_history.js`: Prediction History
- `assets/data/economic_events.js`: 정책금리 차트의 이벤트 설명
- `assets/js/core/shared.js`: 내비게이션, 테마, 공통 등장 효과

정적 파일 URL은 `/static/<assets 아래 상대 경로>` 규칙을 사용합니다. 페이지 URL과
예측 API 계약은 이 디렉터리 구조와 독립적으로 유지됩니다.
