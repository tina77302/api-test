const labelMap = { 인하: "인하", 동결: "동결", 인상: "인상" };
const modelNameMap = {
  random_forest: "Random Forest",
  xgboost: "XGBoost",
};
const featureNameMap = {
  current_rate: "현재 기준금리",
  inflation: "물가상승률",
  exchange_rate: "원·달러 환율",
  unemployment: "실업률",
  bond_3y: "국고채 3년물",
  us_policy_rate: "미국 기준금리",
  inflation_change_1m: "물가 1개월 변화",
  inflation_change_3m: "물가 3개월 변화",
  inflation_change_6m: "물가 6개월 변화",
  exchange_rate_change_1m_pct: "환율 1개월 변화율",
  exchange_rate_change_3m_pct: "환율 3개월 변화율",
  exchange_rate_change_6m_pct: "환율 6개월 변화율",
  bond_3y_change_1m: "국고채 1개월 변화",
  bond_3y_change_3m: "국고채 3개월 변화",
  bond_3y_change_6m: "국고채 6개월 변화",
  korea_us_rate_spread: "한미 기준금리 차",
  bond_policy_spread: "국고채–기준금리 차",
  rate_change_3m: "최근 3개월 금리 변화",
  rate_direction_3m: "최근 3개월 금리 방향",
};

const percent = (value, digits = 1) => `${(Number(value) * 100).toFixed(digits)}%`;
let allHistoryRows = [];
let comparisonHistoryRows = [];

function renderUpdateStatus(status, forecast) {
  const automation = status.automation;
  const stateDot = document.querySelector("#update-state-dot");
  const stateLabel = document.querySelector("#update-state-label");
  const lastUpdate = document.querySelector("#last-update-date");
  const message = document.querySelector("#freshness-message");
  const stepCount = document.querySelector("#completed-step-count");

  document.querySelector("#as-of-date").textContent =
    forecast.analysis_period.latest_input;
  document.querySelector("#update-status").textContent =
    `수집 데이터 기준 ${forecast.analysis_period.latest_input}`;

  if (!automation?.finished_at) {
    stateDot.className = "warning";
    stateLabel.textContent = "업데이트 기록 없음";
    lastUpdate.textContent = "기록 없음";
    stepCount.textContent = "확인 불가";
    message.textContent = "자동 업데이트를 한 번 실행해주세요.";
    message.className = "warning";
    return;
  }

  const finishedAt = new Date(automation.finished_at);
  const elapsedHours = (Date.now() - finishedAt.getTime()) / 3_600_000;
  const isFailed = automation.state === "failed";
  const isStale = elapsedHours > 30;
  lastUpdate.textContent = finishedAt.toLocaleString("ko-KR", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
  stepCount.textContent =
    `${automation.completed_steps?.length ?? 0}단계 완료`;

  if (isFailed) {
    stateDot.className = "error";
    stateLabel.textContent = "업데이트 실패";
    message.textContent =
      `실패 단계: ${automation.current_step ?? "알 수 없음"}`;
    message.className = "error";
  } else if (isStale) {
    stateDot.className = "warning";
    stateLabel.textContent = "업데이트 지연";
    message.textContent =
      `마지막 갱신 후 ${Math.floor(elapsedHours)}시간이 지났습니다.`;
    message.className = "warning";
  } else {
    stateDot.className = "success";
    stateLabel.textContent = "최신 업데이트 완료";
    message.textContent = "모든 데이터 수집과 모델 예측이 정상 완료됐습니다.";
    message.className = "success";
  }
}

function renderReliability(reliability) {
  const prediction = reliability.latest_prediction;
  const assessment = reliability.reliability_assessment;
  const baseline = reliability.validation.baseline_metrics;
  const model = reliability.validation.model_metrics;
  const status = document.querySelector("#reliability-status");
  status.textContent =
    assessment.status === "improved" ? "개선 확인" : "실험 단계";
  status.classList.toggle("improved", assessment.status === "improved");

  document.querySelector("#reliability-result").innerHTML = `
    <div>
      <span>계층형 모델 3개월 전망</span>
      <strong>${prediction.direction}</strong>
    </div>
    ${probabilityBars(prediction.probabilities)}
    <p>
      정확도 ${assessment.beats_baseline_accuracy ? "개선" : "미개선"} ·
      확률 오차 ${assessment.beats_baseline_brier ? "개선" : "미개선"}
    </p>`;

  const rows = [
    ["동결 Baseline", baseline],
    ["계층형 Logistic", model],
  ];
  document.querySelector("#reliability-metrics").innerHTML = rows
    .map(
      ([name, metric]) => `
        <tr>
          <th>${name}</th>
          <td>${percent(metric.accuracy)}</td>
          <td>${Number(metric.macro_f1).toFixed(3)}</td>
          <td>${Number(metric.brier_score).toFixed(3)}</td>
          <td>${percent(metric.cut_recall)}</td>
          <td>${percent(metric.hold_recall)}</td>
          <td>${percent(metric.hike_recall)}</td>
        </tr>`,
    )
    .join("");
}

function renderReliabilityDiagram() {
  const detail = document.querySelector("#reliability-detail");
  const diagrams = {
    history: `<div class="lab-diagram history-expansion">
      <div><span>기존 범위</span><i><b style="width:62%"></b></i><strong>2015 — 2026</strong><small>약 130개월</small></div>
      <div><span>확대 범위</span><i><b style="width:100%"></b></i><strong>2008 — 2026</strong><small>약 220개월</small></div>
      <p><b>추가된 금리 국면</b><span>금융위기 · 장기 저금리 · 코로나 · 급격한 인상</span></p>
    </div>`,
    weight: `<div class="lab-diagram weight-diagram">
      <div><span>과거 데이터</span><i style="opacity:.25"></i><small>낮은 가중치</small></div>
      <div><span>중간 데이터</span><i style="opacity:.55"></i><small>중간 가중치</small></div>
      <div><span>최근 데이터</span><i></i><small>높은 가중치</small></div>
      <p>현재 경제 구조에 가까운 관측치를 더 크게 반영하며, 60개월 전으로 갈 때마다 영향력을 절반으로 줄입니다.</p>
    </div>`,
    hierarchy: `<div class="lab-diagram hierarchy-diagram">
      <div class="flow-input">경제지표 입력<small>물가 · 환율 · 고용 · 시장금리</small></div><i>↓</i>
      <div class="flow-stage"><span>① 금리 변경 여부</span><div><b>동결</b><b>변경</b></div></div><i>↓</i>
      <div class="flow-stage"><span>② 변경 방향</span><div><b class="cut">인하</b><b class="hike">인상</b></div></div>
    </div>`,
    nested: `<div class="lab-diagram nested-diagram">
      <div class="time-arrow"><span>과거</span><i></i><span>미래</span></div>
      <section><strong>내부 검증</strong><div><i class="train short"></i><i class="validation"></i></div><div><i class="train long"></i><i class="validation"></i></div><small>최적 설정 선택</small></section>
      <section><strong>외부 평가</strong><div><i class="train final"></i><i class="test"></i></div><small>최종 성능 평가</small></section>
      <p>모델 설정을 고르는 데이터와 최종 성능을 평가하는 데이터를 분리했습니다.</p>
    </div>`,
  };
  function select(key) {
    document.querySelectorAll("[data-reliability-step]").forEach((button) => button.classList.toggle("active", button.dataset.reliabilityStep === key));
    detail.innerHTML = diagrams[key];
  }
  document.querySelector(".design-flow").addEventListener("click", (event) => {
    const button = event.target.closest("[data-reliability-step]");
    if (button) select(button.dataset.reliabilityStep);
  });
  select("history");
}

function renderRateExplorer(rows, indicator = "none", showUsRate = true) {
  const container = document.querySelector("#rate-comparison-chart");
  const tooltip = document.querySelector("#rate-chart-tooltip");
  const width = 960;
  const padding = 48;
  const mainTop = 18;
  const mainBottom = 248;
  const hasIndicator = indicator !== "none";
  const totalHeight = hasIndicator ? 430 : 290;
  const plotWidth = width - padding * 2;
  const x = (index) => padding + index / Math.max(1, rows.length - 1) * plotWidth;
  const rates = rows.flatMap((row) => showUsRate
    ? [Number(row.current_rate), Number(row.us_policy_rate)]
    : [Number(row.current_rate)]);
  const rateMin = Math.floor(Math.min(...rates) * 2) / 2;
  const rateMax = Math.ceil(Math.max(...rates) * 2) / 2 || 1;
  const rateY = (value) => mainBottom - (value - rateMin) / Math.max(.5, rateMax - rateMin) * (mainBottom - mainTop);
  const path = (field, yScale) => rows.map((row, index) => `${index ? "L" : "M"}${x(index).toFixed(1)},${yScale(Number(row[field])).toFixed(1)}`).join(" ");
  const grid = Array.from({length: 5}, (_, index) => {
    const value = rateMin + (rateMax - rateMin) * index / 4;
    const y = rateY(value);
    return `<line x1="${padding}" y1="${y}" x2="${width-padding}" y2="${y}" class="explorer-grid"/><text x="${padding-8}" y="${y+4}" text-anchor="end" class="explorer-axis">${value.toFixed(1)}%</text>`;
  }).join("");
  const regimes = [
    ["2008-09", "2009-06", "글로벌 금융위기", "crisis"],
    ["2020-02", "2021-12", "코로나19", "covid"],
    ["2021-08", "2023-01", "급격한 금리 인상", "hiking"],
  ];
  const regimeBands = regimes.map(([start, end, label, tone]) => {
    const startIndex = rows.findIndex((row) => row.date >= start);
    let endIndex = rows.findLastIndex((row) => row.date <= end);
    if (startIndex < 0 || endIndex < 0 || endIndex < startIndex) return "";
    endIndex = Math.min(endIndex + 1, rows.length - 1);
    const startX = x(startIndex);
    const bandWidth = Math.max(4, x(endIndex) - startX);
    return `<g class="regime-band ${tone}"><rect x="${startX}" y="${mainTop}" width="${bandWidth}" height="${mainBottom-mainTop}"/><text x="${startX + 5}" y="${mainTop + 14}">${bandWidth > 55 ? label : ""}</text></g>`;
  }).join("");
  const config = {
    inflation: ["inflation", "소비자물가 상승률", "%", "물가와 정책금리의 시차 관계를 비교합니다."],
    exchange_rate: ["exchange_rate", "원·달러 환율", "원", "환율 상승기에 금리 결정 부담이 어떻게 달라졌는지 비교합니다."],
    bond_3y: ["bond_3y", "국고채 3년물", "%", "시장금리가 정책금리에 앞서 움직이는지 비교합니다."],
  }[indicator];
  let subChart = "";
  if (config) {
    const values = rows.map((row) => Number(row[config[0]]));
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);
    const subTop = 302;
    const subBottom = 392;
    const subY = (value) => subBottom - (value - minimum) / Math.max(.01, maximum - minimum) * (subBottom - subTop);
    subChart = `<line x1="${padding}" y1="278" x2="${width-padding}" y2="278" class="explorer-divider"/>
      <text x="${padding}" y="296" class="explorer-label">${config[1]}</text>
      <path d="${path(config[0], subY)}" class="indicator-line"/>
      <text x="${width-padding}" y="296" text-anchor="end" class="explorer-axis">${minimum.toFixed(config[0] === "exchange_rate" ? 0 : 2)} — ${maximum.toFixed(config[0] === "exchange_rate" ? 0 : 2)}${config[2]}</text>`;
  }
  container.innerHTML = `<svg viewBox="0 0 ${width} ${totalHeight}" role="img" aria-label="한국과 미국 기준금리 비교 그래프">
    ${regimeBands}${grid}<path d="${path("current_rate", rateY)}" class="korea-rate-line"/>${showUsRate ? `<path d="${path("us_policy_rate", rateY)}" class="us-rate-line"/>` : ""}
    ${subChart}<line id="explorer-cursor" x1="0" y1="${mainTop}" x2="0" y2="${hasIndicator ? 392 : mainBottom}" class="explorer-cursor" visibility="hidden"/>
    <circle id="explorer-korea-dot" r="5" class="explorer-dot korea" visibility="hidden"/><circle id="explorer-us-dot" r="5" class="explorer-dot usa" visibility="hidden"/>
    <rect x="${padding}" y="${mainTop}" width="${plotWidth}" height="${hasIndicator ? 374 : mainBottom-mainTop}" class="explorer-hit"/>
    <text x="${padding}" y="${totalHeight-8}" class="explorer-axis">${rows[0].date}</text><text x="${width-padding}" y="${totalHeight-8}" text-anchor="end" class="explorer-axis">${rows.at(-1).date}</text>
  </svg>`;
  document.querySelector("#indicator-explanation").textContent = config?.[3] ?? "한국과 미국의 정책금리 흐름 및 한미 금리 차를 비교합니다.";
  const svg = container.querySelector("svg");
  const cursor = svg.querySelector("#explorer-cursor");
  const koreaDot = svg.querySelector("#explorer-korea-dot");
  const usDot = svg.querySelector("#explorer-us-dot");
  svg.addEventListener("pointermove", (event) => {
    const rect = svg.getBoundingClientRect();
    const svgX = (event.clientX - rect.left) / rect.width * width;
    const index = Math.min(rows.length - 1, Math.max(0, Math.round((svgX - padding) / plotWidth * (rows.length - 1))));
    const row = rows[index];
    const pointX = x(index);
    cursor.setAttribute("x1", pointX); cursor.setAttribute("x2", pointX); cursor.setAttribute("visibility", "visible");
    const visibleDots = [[koreaDot, row.current_rate]];
    if (showUsRate) visibleDots.push([usDot, row.us_policy_rate]);
    visibleDots.forEach(([dot, value]) => { dot.setAttribute("cx", pointX); dot.setAttribute("cy", rateY(Number(value))); dot.setAttribute("visibility", "visible"); });
    const date = new Intl.DateTimeFormat("ko-KR", {year:"numeric", month:"long"}).format(new Date(`${row.date}-01T00:00:00`));
    const indicatorRow = config ? `<div><span>${config[1]}</span><strong>${Number(row[config[0]]).toFixed(config[0] === "exchange_rate" ? 1 : 2)}${config[2]}</strong></div>` : "";
    const usRows = showUsRate ? `<div><span>미국 기준금리</span><strong>${Number(row.us_policy_rate).toFixed(2)}%</strong></div><div><span>한미 금리 차</span><strong>${(Number(row.current_rate)-Number(row.us_policy_rate)).toFixed(2)}%p</strong></div>` : "";
    tooltip.innerHTML = `<b>${date}</b><div><span>한국 기준금리</span><strong>${Number(row.current_rate).toFixed(2)}%</strong></div>${usRows}${indicatorRow}`;
    tooltip.hidden = false;
    tooltip.style.left = `${Math.min(82, Math.max(18, pointX / width * 100))}%`;
  });
  svg.addEventListener("pointerleave", () => { tooltip.hidden = true; [cursor, koreaDot, usDot].forEach((item) => item.setAttribute("visibility", "hidden")); });
}

function initializeRateExplorer(rows) {
  comparisonHistoryRows = rows;
  let selectedPeriod = "all";
  let selectedIndicator = "none";
  let showUsRate = true;
  function update() {
    const count = selectedPeriod === "all" ? rows.length : Number(selectedPeriod);
    renderRateExplorer(rows.slice(-count), selectedIndicator, showUsRate);
  }
  document.querySelector(".indicator-tabs").addEventListener("click", (event) => {
    const button = event.target.closest("[data-indicator]");
    if (!button) return;
    document.querySelectorAll("[data-indicator]").forEach((item) => item.classList.toggle("active", item === button));
    selectedIndicator = button.dataset.indicator;
    update();
  });
  document.querySelector(".range-tabs").addEventListener("click", (event) => {
    const button = event.target.closest("[data-rate-period]");
    if (!button) return;
    document.querySelectorAll("[data-rate-period]").forEach((item) => item.classList.toggle("active", item === button));
    selectedPeriod = button.dataset.ratePeriod;
    update();
  });
  document.querySelector("#us-rate-toggle").addEventListener("change", (event) => {
    showUsRate = event.target.checked;
    document.querySelector(".rate-legend span:last-child").classList.toggle("muted", !showUsRate);
    update();
  });
  update();
}

function topDirection(probabilities) {
  return Object.entries(probabilities).sort((a, b) => b[1] - a[1])[0];
}

function renderModelClassroom(forecast, reliability) {
  const forest = forecast.models.random_forest;
  const boost = forecast.models.xgboost;
  const hierarchy = reliability.latest_prediction;
  const ensemble = forecast.latest_ensemble;
  const featureList = (model) => model.top_features.slice(0, 3)
    .map((item) => featureNameMap[item.feature] ?? item.feature).join(" · ");
  const params = (items) => Object.entries(items).map(([key, value]) => `<span><b>${key}</b>${value}</span>`).join("");
  const probabilitySummary = (probabilities) => ["인하", "동결", "인상"]
    .map((label) => `<div class="lesson-probability ${label}"><span>${label}</span><i><b style="width:${Number(probabilities[label]) * 100}%"></b></i><strong>${percent(probabilities[label])}</strong></div>`).join("");
  const [forestDirection] = topDirection(forest.latest_probabilities);
  const [boostDirection] = topDirection(boost.latest_probabilities);
  const lessons = {
    random_forest: {
      kicker: "여러 의사결정나무의 다수결",
      title: "Random Forest",
      flow: ["월별 경제지표 19개", "서로 다른 표본·변수로 여러 나무 학습", "각 나무가 인하·동결·인상에 투표", "나무별 확률을 평균"],
      formula: "P(방향) = 모든 의사결정나무가 낸 방향별 확률의 평균",
      params: forest.best_params,
      probabilities: forest.latest_probabilities,
      interpretation: `현재 가장 높은 선택은 ${forestDirection}입니다. 모델이 크게 참고한 변수는 ${featureList(forest)}입니다. 비선형 관계와 변수 간 조합을 포착하는 데 유리합니다.`,
      conclusion: `시간순 검증 정확도는 ${percent(forest.cv_metrics.accuracy)}, Macro F1은 ${Number(forest.cv_metrics.macro_f1).toFixed(3)}입니다. 단순 동결 기준보다 나은지 반드시 함께 비교해야 합니다.`,
      limitation: "변수 중요도는 인과관계가 아닙니다. 표본이 작으면 나무 구성이 바뀔 때 확률과 순위도 크게 달라질 수 있습니다.",
    },
    xgboost: {
      kicker: "이전 나무의 오류를 순차 보정",
      title: "XGBoost",
      flow: ["월별 경제지표 19개", "첫 번째 작은 나무가 초기 분류", "틀린 사례에 다음 나무가 집중", "보정값을 누적해 방향 확률 계산"],
      formula: "최종 점수 = 첫 예측 + 학습률 × 각 보정 나무의 점수",
      params: boost.best_params,
      probabilities: boost.latest_probabilities,
      interpretation: `현재 가장 높은 선택은 ${boostDirection}입니다. 주요 신호는 ${featureList(boost)}입니다. 작은 변화가 연속적으로 누적되는 패턴을 학습하는 데 강점이 있습니다.`,
      conclusion: `시간순 검증 정확도는 ${percent(boost.cv_metrics.accuracy)}, Macro F1은 ${Number(boost.cv_metrics.macro_f1).toFixed(3)}입니다. 현재 데이터에서는 인상 사례 탐지 성능을 충분히 검증하지 못했습니다.`,
      limitation: "적은 표본에서 반복 보정하면 과거 잡음까지 학습할 수 있습니다. 학습률과 나무 깊이에 따라 결과가 민감하게 바뀝니다.",
    },
    hierarchical: {
      kicker: "변경 여부와 방향을 나눠 계산",
      title: "계층형 Logistic",
      flow: ["2008년 이후 자료에 최근 가중치 적용", "1단계: 변경 또는 동결 확률", "2단계: 변경 조건에서 인하 또는 인상", "두 단계 확률을 곱해 최종 3방향 확률"],
      formula: "P(인하) = P(변경) × P(인하 | 변경)",
      params: {"1단계 C": reliability.selected_params.change_vs_hold.C, "2단계 C": reliability.selected_params.cut_vs_hike.C, "최근 가중 반감기": "60개월"},
      probabilities: hierarchy.probabilities,
      interpretation: `동결이 많은 금리 데이터의 특성을 반영해 먼저 변경 여부를 묻습니다. 현재 결과는 ${hierarchy.direction}이며, 각 단계의 계수 방향을 통해 신호를 비교적 쉽게 설명할 수 있습니다.`,
      conclusion: `검증 정확도 ${percent(reliability.validation.model_metrics.accuracy)}, Macro F1 ${Number(reliability.validation.model_metrics.macro_f1).toFixed(3)}, Brier Score ${Number(reliability.validation.model_metrics.brier_score).toFixed(3)}입니다.`,
      limitation: "변수와 결과 사이가 직선적인 로그오즈 관계라고 가정합니다. 복잡한 임계점과 변수 조합을 충분히 표현하지 못할 수 있습니다.",
    },
    ensemble: {
      kicker: "서로 다른 모델의 확률을 동일 비중 결합",
      title: "Random Forest + XGBoost 평균",
      flow: ["Random Forest 방향 확률", "XGBoost 방향 확률", "방향별 확률을 50:50 평균", "가장 높은 평균 확률을 기본 시나리오로 선택"],
      formula: "P앙상블(방향) = [PRF(방향) + PXGB(방향)] ÷ 2",
      params: {"Random Forest": "50%", "XGBoost": "50%", "확률 보정": "미적용"},
      probabilities: ensemble.probabilities,
      interpretation: `두 모델의 서로 다른 오류를 완화하려는 방식입니다. 현재 기본 시나리오는 ${ensemble.direction}이지만, 모델 간 의견이 다르면 평균값만 보고 강한 합의로 해석하면 안 됩니다.`,
      conclusion: `Random Forest는 ${forestDirection}, XGBoost는 ${boostDirection}을 가장 높게 봅니다. ${forestDirection === boostDirection ? "두 모델의 1순위 방향이 일치합니다." : "두 모델의 1순위 방향이 달라 불확실성이 큽니다."}`,
      limitation: "두 모델이 같은 데이터와 유사한 변수로 학습하므로 완전히 독립적이지 않습니다. 평균 확률은 실제 발생 확률로 보정된 값이 아닙니다.",
    },
  };
  function selectLesson(key) {
    const lesson = lessons[key];
    document.querySelectorAll("[data-model-lesson]").forEach((button) => button.classList.toggle("active", button.dataset.modelLesson === key));
    document.querySelector("#model-lesson").innerHTML = `<div class="lesson-header"><span>${lesson.kicker}</span><h3>${lesson.title}</h3></div>
      <div class="calculation-flow">${lesson.flow.map((step, index) => `<div><span>0${index + 1}</span><strong>${step}</strong></div>${index < lesson.flow.length - 1 ? "<i>→</i>" : ""}`).join("")}</div>
      <code class="model-formula">${lesson.formula}</code>
      <div class="lesson-layout"><div><h4>현재 방향 확률</h4>${probabilitySummary(lesson.probabilities)}</div><div><h4>실제 적용 설정</h4><div class="parameter-chips">${params(lesson.params)}</div></div></div>
      <div class="lesson-conclusions"><article><span>해석</span><p>${lesson.interpretation}</p></article><article><span>검증과 결론</span><p>${lesson.conclusion}</p></article><article class="warning"><span>한계</span><p>${lesson.limitation}</p></article></div>`;
  }
  document.querySelector(".model-tabs").addEventListener("click", (event) => {
    const button = event.target.closest("[data-model-lesson]");
    if (button) selectLesson(button.dataset.modelLesson);
  });
  selectLesson("random_forest");
}

function renderUncertaintyAnalysis(forecast, reliability, rows) {
  const modelDirections = Object.values(forecast.models).map((model) => topDirection(model.latest_probabilities)[0]);
  modelDirections.push(reliability.latest_prediction.direction);
  const agreementCount = Math.max(...["인하", "동결", "인상"].map((label) => modelDirections.filter((item) => item === label).length));
  const ranking = Object.values(forecast.latest_ensemble.probabilities).sort((a, b) => b - a);
  const margin = ranking[0] - ranking[1];
  const latest = rows.at(-1);
  const fields = ["inflation", "exchange_rate", "bond_3y", "us_policy_rate"];
  const extremeFields = fields.filter((field) => {
    const values = rows.map((row) => Number(row[field]));
    const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
    const deviation = Math.sqrt(values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length) || 1;
    return Math.abs((Number(latest[field]) - mean) / deviation) > 2;
  });
  const baseline = forecast.validation.hold_baseline_metrics.accuracy;
  const modelsBelowBaseline = Object.values(forecast.models).every((model) => model.cv_metrics.accuracy < baseline);
  const score = Number(agreementCount < 3) + Number(margin < .15) + Number(extremeFields.length > 0) + Number(modelsBelowBaseline);
  const levels = ["낮음", "보통", "높음", "매우 높음"];
  const level = levels[Math.min(score, 3)];
  const levelElement = document.querySelector("#uncertainty-level");
  levelElement.textContent = `${level} 불확실성`;
  levelElement.dataset.level = level;
  const checks = [
    ["모델 합의", `${agreementCount}/3개 모델이 같은 방향`, agreementCount === 3 ? "good" : "warn"],
    ["시나리오 간격", `1·2순위 차이 ${percent(margin)}`, margin >= .15 ? "good" : "warn"],
    ["과거 범위 비교", extremeFields.length ? `${extremeFields.map((field) => featureNameMap[field]).join("·")} 이례적` : "주요 지표가 과거 범위 안", extremeFields.length ? "warn" : "good"],
    ["Baseline 비교", modelsBelowBaseline ? "두 모델 모두 단순 기준 미달" : "일부 모델이 단순 기준 상회", modelsBelowBaseline ? "danger" : "good"],
  ];
  document.querySelector("#uncertainty-analysis").innerHTML = `<div class="uncertainty-checks">${checks.map(([name, value, tone]) => `<div class="${tone}"><span>${name}</span><strong>${value}</strong></div>`).join("")}</div>
    <p><b>종합 해석</b> 현재 불확실성은 <strong>${level}</strong> 수준으로 평가됩니다. 이 평가는 모델의 의견 차이와 과거 검증 상태를 설명하는 지표이며, 블랙스완의 발생 확률을 계산한 값은 아닙니다.</p>`;
}

function lineChart(rows, field, unit, color) {
  const values = rows.map((row) => Number(row[field])).filter(Number.isFinite);
  if (!values.length) return "";
  const width = 320;
  const height = 130;
  const padding = 14;
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const range = maximum - minimum || 1;
  const x = (index) =>
    padding + (index / Math.max(1, values.length - 1)) * (width - padding * 2);
  const y = (value) =>
    height - padding - ((value - minimum) / range) * (height - padding * 2);
  const points = values.map((value, index) => `${x(index)},${y(value)}`).join(" ");
  const latest = values.at(-1);
  const hoverPoints = values
    .map((value, index) => `
      <circle class="hover-point" cx="${x(index)}" cy="${y(value)}" r="8">
        <title>${rows[index].date} · ${value.toFixed(field === "exchange_rate" ? 1 : 2)}${unit}</title>
      </circle>`)
    .join("");
  return `
    <svg viewBox="0 0 ${width} ${height}" role="img">
      <polyline points="${points}" fill="none" stroke="${color}" stroke-width="2.5" />
      ${hoverPoints}
      <circle cx="${x(values.length - 1)}" cy="${y(latest)}" r="4" fill="${color}" />
      <text x="${width - padding}" y="${padding}" text-anchor="end" class="spark-value">
        ${latest.toFixed(field === "exchange_rate" ? 1 : 2)}${unit}
      </text>
      <text x="${padding}" y="${height - 1}" class="spark-date">${rows[0].date}</text>
      <text x="${width - padding}" y="${height - 1}" text-anchor="end" class="spark-date">${rows.at(-1).date}</text>
    </svg>`;
}

function renderIndicatorCharts(rows) {
  const indicators = [
    ["inflation", "소비자물가 상승률", "%", "#cfff5a"],
    ["exchange_rate", "원·달러 환율", "원", "#63a6ff"],
    ["bond_3y", "국고채 3년물", "%", "#ffc45d"],
    ["us_policy_rate", "미국 기준금리", "%", "#ff705d"],
  ];
  document.querySelector("#indicator-charts").innerHTML = indicators
    .map(
      ([field, title, unit, color]) => `
        <article class="indicator-card">
          <h3>${title}</h3>
          ${lineChart(rows, field, unit, color)}
        </article>`,
    )
    .join("");
}

function groupedBars(groups, series, formatter = percent) {
  const colors = ["#63a6ff", "#929a94", "#ff705d"];
  return `
    <div class="grouped-bars">
      ${groups
        .map(
          (group) => `
            <div class="bar-group">
              <div class="bar-cluster">
                ${series
                  .map(
                    (item, index) => `
                      <div class="vertical-bar-wrap">
                        <span>${formatter(item.values[group])}</span>
                        <i style="height:${Math.max(2, Number(item.values[group]) * 100)}%;background:${colors[index]}"></i>
                      </div>`,
                  )
                  .join("")}
              </div>
              <strong>${group}</strong>
            </div>`,
        )
        .join("")}
    </div>
    <div class="chart-legend">
      ${series
        .map(
          (item, index) =>
            `<span><i style="background:${colors[index]}"></i>${item.name}</span>`,
        )
        .join("")}
    </div>`;
}

function renderComparisonCharts(forecast) {
  const probabilitySeries = [
    {
      name: "Random Forest",
      values: forecast.models.random_forest.latest_probabilities,
    },
    {
      name: "XGBoost",
      values: forecast.models.xgboost.latest_probabilities,
    },
    {
      name: "모델 평균",
      values: forecast.latest_ensemble.probabilities,
    },
  ];
  document.querySelector("#model-probability-chart").innerHTML = groupedBars(
    ["인하", "동결", "인상"],
    probabilitySeries,
  );

  const baseline = forecast.validation.hold_baseline_metrics;
  const performanceSeries = [
    {
      name: "Baseline",
      values: { 정확도: baseline.accuracy, "Macro F1": baseline.macro_f1 },
    },
    {
      name: "Random Forest",
      values: {
        정확도: forecast.models.random_forest.cv_metrics.accuracy,
        "Macro F1": forecast.models.random_forest.cv_metrics.macro_f1,
      },
    },
    {
      name: "XGBoost",
      values: {
        정확도: forecast.models.xgboost.cv_metrics.accuracy,
        "Macro F1": forecast.models.xgboost.cv_metrics.macro_f1,
      },
    },
  ];
  document.querySelector("#performance-chart").innerHTML = groupedBars(
    ["정확도", "Macro F1"],
    performanceSeries,
  );
}

function renderAnalysisExplanation(forecast) {
  const probabilities = forecast.latest_ensemble.probabilities;
  const ranking = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);
  const [firstLabel, firstValue] = ranking[0];
  const [secondLabel, secondValue] = ranking[1];
  const margin = firstValue - secondValue;
  const baseline = forecast.validation.hold_baseline_metrics;
  const forest = forecast.models.random_forest.cv_metrics;
  const xgboost = forecast.models.xgboost.cv_metrics;
  const distribution = forecast.validation.test_label_distribution;
  const noHikeSamples = !distribution.인상;

  document.querySelector("#analysis-summary").innerHTML = `
    <span class="result-kicker">3개월 기본 시나리오</span>
    <strong>${firstLabel}</strong>
    <p>
      모델 평균은 <b>${firstLabel} ${percent(firstValue)}</b>를 가장 높게 봅니다.
      두 번째 시나리오인 ${secondLabel} ${percent(secondValue)}와의 차이는
      <b>${percent(margin)}</b>입니다.
    </p>`;

  document.querySelector("#analysis-details").innerHTML = `
    <div>
      <dt>학습 기간</dt>
      <dd>${forecast.analysis_period.start} — ${forecast.analysis_period.training_end}</dd>
    </div>
    <div>
      <dt>학습 표본</dt>
      <dd>${forecast.analysis_period.training_samples}개월</dd>
    </div>
    <div>
      <dt>Baseline 정확도</dt>
      <dd>${percent(baseline.accuracy)}</dd>
    </div>
    <div>
      <dt>Random Forest 정확도</dt>
      <dd>${percent(forest.accuracy)}</dd>
    </div>
    <div>
      <dt>XGBoost 정확도</dt>
      <dd>${percent(xgboost.accuracy)}</dd>
    </div>
    <div>
      <dt>검증 정답 분포</dt>
      <dd>인하 ${distribution.인하 ?? 0} · 동결 ${distribution.동결 ?? 0} · 인상 ${distribution.인상 ?? 0}</dd>
    </div>`;

  const confidenceLabel = document.querySelector("#confidence-label");
  const confidenceReason = document.querySelector("#confidence-reason");
  if (
    forest.accuracy < baseline.accuracy &&
    xgboost.accuracy < baseline.accuracy
  ) {
    confidenceLabel.textContent = "낮음 · 실험 단계";
    confidenceLabel.className = "low";
    confidenceReason.textContent =
      `두 머신러닝 모델 모두 동결 Baseline보다 검증 정확도가 낮습니다.${
        noHikeSamples
          ? " 검증 기간에 실제 인상 사례도 없어 인상 탐지 능력을 평가할 수 없습니다."
          : ""
      }`;
  } else if (margin < 0.15) {
    confidenceLabel.textContent = "보통 이하 · 시나리오 경합";
    confidenceLabel.className = "medium";
    confidenceReason.textContent =
      "1순위와 2순위 확률 차이가 작아 방향이 뚜렷하지 않습니다.";
  } else {
    confidenceLabel.textContent = "보통 · 추가 검증 필요";
    confidenceLabel.className = "medium";
    confidenceReason.textContent =
      "현재 모델에서는 방향성이 나타나지만 더 많은 기간의 검증이 필요합니다.";
  }
}

function probabilityBars(probabilities) {
  return ["인하", "동결", "인상"]
    .map(
      (label) => `
        <div class="probability-row ${label}">
          <div><span>${labelMap[label]}</span><strong>${percent(probabilities[label])}</strong></div>
          <div class="track"><i style="width:${Number(probabilities[label]) * 100}%"></i></div>
        </div>`,
    )
    .join("");
}

function renderHistory(rows) {
  const container = document.querySelector("#history-chart");
  const values = rows.map((row) => Number(row.current_rate));
  const width = 760;
  const height = 280;
  const padding = 32;
  const min = Math.min(...values) - 0.15;
  const max = Math.max(...values) + 0.15;
  const x = (index) =>
    padding + (index / Math.max(1, values.length - 1)) * (width - padding * 2);
  const y = (value) =>
    height - padding - ((value - min) / (max - min)) * (height - padding * 2);
  const points = values.map((value, index) => `${x(index)},${y(value)}`).join(" ");
  const area = `${padding},${height - padding} ${points} ${width - padding},${height - padding}`;
  const last = rows.at(-1);
  const hoverPoints = rows.map((row, index) => `
    <circle class="hover-point" cx="${x(index)}" cy="${y(values[index])}" r="10">
      <title>${row.date} · 기준금리 ${values[index].toFixed(2)}%</title>
    </circle>`).join("");

  container.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="최근 ${rows.length}개월 기준금리">
      <defs>
        <linearGradient id="area-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#cfff5a" stop-opacity=".28" />
          <stop offset="100%" stop-color="#cfff5a" stop-opacity="0" />
        </linearGradient>
      </defs>
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" class="axis" />
      <polygon points="${area}" fill="url(#area-fill)" />
      <polyline points="${points}" class="rate-line" />
      ${hoverPoints}
      <circle cx="${x(values.length - 1)}" cy="${y(values.at(-1))}" r="6" class="last-dot" />
      <text x="${x(values.length - 1) - 8}" y="${y(values.at(-1)) - 14}" text-anchor="end" class="chart-value">${values.at(-1).toFixed(2)}%</text>
      <text x="${padding}" y="${height - 8}" class="chart-label">${rows[0].date}</text>
      <text x="${width - padding}" y="${height - 8}" text-anchor="end" class="chart-label">${last.date}</text>
    </svg>`;
}

function changeLabel(value, unit = "%p") {
  const number = Number(value);
  const arrow = number > 0 ? "↑" : number < 0 ? "↓" : "→";
  return `${arrow} ${Math.abs(number).toFixed(2)}${unit}`;
}

function renderDecisionDrivers(rows, forecast) {
  const latest = rows.at(-1);
  const prior3 = rows.at(-4) ?? rows[0];
  const signals = [
    {
      name: "물가 압력",
      value: `${Number(latest.inflation).toFixed(2)}%`,
      change: Number(latest.inflation) - Number(prior3.inflation),
      text: "3개월 물가 변화",
      tone: Number(latest.inflation) > Number(prior3.inflation) ? "hike" : "cut",
    },
    {
      name: "원·달러 환율",
      value: `${Number(latest.exchange_rate).toLocaleString("ko-KR", {maximumFractionDigits: 1})}원`,
      change: ((Number(latest.exchange_rate) / Number(prior3.exchange_rate)) - 1) * 100,
      text: "3개월 환율 변화",
      tone: Number(latest.exchange_rate) > Number(prior3.exchange_rate) ? "hike" : "cut",
      unit: "%",
    },
    {
      name: "채권시장 기대",
      value: `${(Number(latest.bond_3y) - Number(latest.current_rate)).toFixed(2)}%p`,
      change: Number(latest.bond_3y) - Number(latest.current_rate),
      text: "3년물−기준금리",
      tone: Number(latest.bond_3y) >= Number(latest.current_rate) ? "hike" : "cut",
    },
    {
      name: "한·미 금리차",
      value: `${(Number(latest.current_rate) - Number(latest.us_policy_rate)).toFixed(2)}%p`,
      change: Number(latest.current_rate) - Number(latest.us_policy_rate),
      text: "한국−미국 정책금리",
      tone: Number(latest.current_rate) < Number(latest.us_policy_rate) ? "hike" : "neutral",
    },
  ];
  document.querySelector("#driver-cards").innerHTML = signals.map((item) => `
    <article class="driver-card ${item.tone}">
      <span>${item.name}</span><strong>${item.value}</strong>
      <small>${item.text} · ${changeLabel(item.change, item.unit ?? "%p")}</small>
    </article>`).join("");

  const probabilities = forecast.latest_ensemble.probabilities;
  document.querySelector("#scenario-list").innerHTML = [
    ["인하", probabilities.인하, "물가 둔화와 경기·고용 약화가 뚜렷해질 때"],
    ["동결", probabilities.동결, "물가와 환율 부담 속에서 관망이 필요할 때"],
    ["인상", probabilities.인상, "물가 재상승·원화 약세·시장금리 상승이 겹칠 때"],
  ].map(([name, value, condition]) => `
    <div class="scenario-item ${name}"><span>${name}</span><strong>${percent(value)}</strong><p>${condition}</p></div>`).join("");
}

function renderFoldTimeline(forecast) {
  const models = Object.entries(forecast.models);
  const foldCount = Math.max(...models.map(([, model]) => model.folds.length));
  const timeline = document.querySelector("#fold-timeline");
  const range = document.querySelector("#timeline-range");
  const previous = document.querySelector("#timeline-prev");
  const next = document.querySelector("#timeline-next");
  let selectedIndex = foldCount - 1;

  range.max = String(foldCount - 1);
  range.value = String(selectedIndex);
  timeline.innerHTML = Array.from({length: foldCount}, (_, index) => `
    <button class="timeline-node" type="button" role="tab" data-fold="${index}" aria-selected="false">
      <i></i><span>FOLD ${String(index + 1).padStart(2, "0")}</span>
    </button>`).join("");

  function selectFold(index) {
    selectedIndex = Math.min(Math.max(index, 0), foldCount - 1);
    const sample = models[0][1].folds[selectedIndex];
    range.value = String(selectedIndex);
    previous.disabled = selectedIndex === 0;
    next.disabled = selectedIndex === foldCount - 1;
    document.querySelector("#timeline-position").textContent =
      `${selectedIndex + 1} / ${foldCount} 구간 · ${sample.train_samples}개월 학습 → ${sample.test_samples}개월 평가`;
    timeline.querySelectorAll(".timeline-node").forEach((node, index) => {
      const active = index === selectedIndex;
      node.classList.toggle("active", active);
      node.setAttribute("aria-selected", String(active));
    });

    document.querySelector("#timeline-detail").innerHTML = models.map(([name, model]) => {
      const metrics = model.folds[selectedIndex].metrics;
      const recalls = [
        ["인하", metrics.cut_recall, "cut"],
        ["동결", metrics.hold_recall, "hold"],
        ["인상", metrics.hike_recall, "hike"],
      ];
      return `<article>
        <header><div><span>${modelNameMap[name]}</span><small>FOLD ${String(selectedIndex + 1).padStart(2, "0")}</small></div><strong>${percent(metrics.accuracy)}</strong></header>
        <div class="timeline-score"><span>정확도</span><i><b style="width:${Number(metrics.accuracy) * 100}%"></b></i></div>
        <div class="timeline-score"><span>Macro F1</span><i><b style="width:${Number(metrics.macro_f1) * 100}%"></b></i><em>${Number(metrics.macro_f1).toFixed(3)}</em></div>
        <div class="recall-grid">${recalls.map(([label, value, tone]) => `<div class="${tone}"><span>${label} 탐지율</span><strong>${percent(value)}</strong></div>`).join("")}</div>
      </article>`;
    }).join("");
  }

  timeline.addEventListener("click", (event) => {
    const node = event.target.closest("[data-fold]");
    if (node) selectFold(Number(node.dataset.fold));
  });
  range.addEventListener("input", () => selectFold(Number(range.value)));
  previous.addEventListener("click", () => selectFold(selectedIndex - 1));
  next.addEventListener("click", () => selectFold(selectedIndex + 1));
  selectFold(selectedIndex);
}

function renderWatchList(rows) {
  const latest = rows.at(-1);
  const items = [
    ["물가", `${Number(latest.inflation).toFixed(2)}%`, "둔화 지속 여부"],
    ["환율", `${Number(latest.exchange_rate).toFixed(1)}원`, "원화 약세 압력"],
    ["국고채 3년", `${Number(latest.bond_3y).toFixed(2)}%`, "정책금리 선행 신호"],
    ["미국 정책금리", `${Number(latest.us_policy_rate).toFixed(2)}%`, "한미 금리차 변화"],
  ];
  document.querySelector("#watch-list").innerHTML = items.map(([name, value, note], index) => `
    <div><span>0${index + 1}</span><p><strong>${name}</strong><small>${note}</small></p><b>${value}</b></div>`).join("");
}

function renderModel(name, model) {
  const direction = model.latest_probabilities;
  return `
    <article class="model-card">
      <div class="model-title">
        <span>${modelNameMap[name]}</span>
        <strong>${Object.entries(direction).sort((a, b) => b[1] - a[1])[0][0]}</strong>
      </div>
      ${probabilityBars(direction)}
    </article>`;
}

function renderFeatureColumn(name, features) {
  const maximum = Math.max(...features.map((item) => Number(item.importance)));
  return `
    <article>
      <h3>${modelNameMap[name]}</h3>
      ${features
        .map(
          (item, index) => `
            <div class="feature-row">
              <span>${index + 1}</span>
              <div>
                <strong>${featureNameMap[item.feature] ?? item.feature}</strong>
                <i style="width:${(Number(item.importance) / maximum) * 100}%"></i>
              </div>
              <small>${Number(item.importance).toFixed(3)}</small>
            </div>`,
        )
        .join("")}
    </article>`;
}

async function loadDashboard() {
  try {
    const [
      forecastResponse,
      reliabilityResponse,
      historyResponse,
      statusResponse,
    ] = await Promise.all([
      fetch("/forecast/latest"),
      fetch("/forecast/reliability"),
      fetch("/forecast/history?months=360"),
      fetch("/forecast/status"),
    ]);
    if (
      !forecastResponse.ok ||
      !reliabilityResponse.ok ||
      !historyResponse.ok ||
      !statusResponse.ok
    ) {
      throw new Error("예측 데이터를 불러오지 못했습니다.");
    }

    const forecast = await forecastResponse.json();
    const reliability = await reliabilityResponse.json();
    const history = await historyResponse.json();
    const status = await statusResponse.json();
    const ensemble = forecast.latest_ensemble;
    const lastHistory = history.rows.at(-1);

    document.querySelector("#current-rate").textContent =
      `${Number(lastHistory.current_rate).toFixed(2)}%`;
    document.querySelector("#ensemble-direction").textContent =
      ensemble.direction;
    document.querySelector("#hold-probability").textContent =
      percent(ensemble.probabilities.동결);
    document.querySelector("#ensemble-bars").innerHTML =
      probabilityBars(ensemble.probabilities);
    document.querySelector("#footer-period").textContent =
      `학습 ${forecast.analysis_period.start} — ${forecast.analysis_period.training_end}`;

    renderUpdateStatus(status, forecast);

    const defaultHistoryRows = history.rows.slice(-36);
    renderHistory(defaultHistoryRows);
    allHistoryRows = defaultHistoryRows;
    renderIndicatorCharts(allHistoryRows);
    initializeRateExplorer(history.rows);
    renderDecisionDrivers(allHistoryRows, forecast);
    renderFoldTimeline(forecast);
    renderWatchList(allHistoryRows);
    renderComparisonCharts(forecast);
    renderAnalysisExplanation(forecast);
    renderReliability(reliability);
    renderReliabilityDiagram();
    renderModelClassroom(forecast, reliability);
    renderUncertaintyAnalysis(forecast, reliability, history.rows);
    document.querySelector("#model-cards").innerHTML = Object.entries(
      forecast.models,
    )
      .map(([name, model]) => renderModel(name, model))
      .join("");

    const baseline = forecast.validation.hold_baseline_metrics;
    const metricRows = [
      ["동결 Baseline", baseline],
      ...Object.entries(forecast.models).map(([name, model]) => [
        modelNameMap[name],
        model.cv_metrics,
      ]),
    ];
    document.querySelector("#metrics-body").innerHTML = metricRows
      .map(
        ([name, metric]) => `
          <tr>
            <th>${name}</th>
            <td>${percent(metric.accuracy)}</td>
            <td>${Number(metric.macro_f1).toFixed(3)}</td>
            <td>${percent(metric.cut_recall)}</td>
            <td>${percent(metric.hold_recall)}</td>
            <td>${percent(metric.hike_recall)}*</td>
          </tr>`,
      )
      .join("");

    document.querySelector("#feature-columns").innerHTML = Object.entries(
      forecast.models,
    )
      .map(([name, model]) => renderFeatureColumn(name, model.top_features))
      .join("");
  } catch (error) {
    document.querySelector("#update-status").textContent = error.message;
    document.querySelector("#history-chart").innerHTML =
      `<div class="error-state"><strong>대시보드를 연결하지 못했습니다</strong><p>${error.message}</p><button type="button" onclick="location.reload()">다시 시도</button></div>`;
  }
}

document.querySelectorAll(".period-selector button").forEach((button) => {
  button.addEventListener("click", async () => {
    document
      .querySelectorAll(".period-selector button")
      .forEach((item) => item.classList.toggle("active", item === button));
    const months = Number(button.dataset.months);
    try {
      const response = await fetch(`/forecast/history?months=${months}`);
      if (!response.ok) throw new Error("기간 데이터를 불러오지 못했습니다.");
      const payload = await response.json();
      allHistoryRows = payload.rows;
      renderHistory(allHistoryRows);
      renderIndicatorCharts(allHistoryRows);
    } catch (error) {
      document.querySelector("#indicator-charts").innerHTML =
        `<p class="error">${error.message}</p>`;
    }
  });
});

const savedTheme = localStorage.getItem("ratescope-theme");
if (savedTheme === "light") document.documentElement.dataset.theme = "light";
document.querySelector("#theme-toggle").addEventListener("click", () => {
  const light = document.documentElement.dataset.theme !== "light";
  document.documentElement.dataset.theme = light ? "light" : "dark";
  localStorage.setItem("ratescope-theme", light ? "light" : "dark");
});

const glossaryDialog = document.querySelector("#glossary-dialog");
document.querySelector("#glossary-open").addEventListener("click", () => glossaryDialog.showModal());
document.querySelector("#glossary-close").addEventListener("click", () => glossaryDialog.close());
glossaryDialog.addEventListener("click", (event) => {
  if (event.target === glossaryDialog) glossaryDialog.close();
});

loadDashboard();
