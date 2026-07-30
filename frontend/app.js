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
  return `
    <svg viewBox="0 0 ${width} ${height}" role="img">
      <polyline points="${points}" fill="none" stroke="${color}" stroke-width="2.5" />
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
      <circle cx="${x(values.length - 1)}" cy="${y(values.at(-1))}" r="6" class="last-dot" />
      <text x="${x(values.length - 1) - 8}" y="${y(values.at(-1)) - 14}" text-anchor="end" class="chart-value">${values.at(-1).toFixed(2)}%</text>
      <text x="${padding}" y="${height - 8}" class="chart-label">${rows[0].date}</text>
      <text x="${width - padding}" y="${height - 8}" text-anchor="end" class="chart-label">${last.date}</text>
    </svg>`;
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
    const [forecastResponse, historyResponse, statusResponse] = await Promise.all([
      fetch("/forecast/latest"),
      fetch("/forecast/history?months=36"),
      fetch("/forecast/status"),
    ]);
    if (!forecastResponse.ok || !historyResponse.ok || !statusResponse.ok) {
      throw new Error("예측 데이터를 불러오지 못했습니다.");
    }

    const forecast = await forecastResponse.json();
    const history = await historyResponse.json();
    const status = await statusResponse.json();
    const ensemble = forecast.latest_ensemble;
    const lastHistory = history.rows.at(-1);

    document.querySelector("#as-of-date").textContent =
      forecast.analysis_period.latest_input;
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

    const updated = status.forecast_updated_at
      ? new Date(status.forecast_updated_at).toLocaleString("ko-KR")
      : "기록 없음";
    document.querySelector("#update-status").textContent = `결과 생성: ${updated}`;

    renderHistory(history.rows);
    allHistoryRows = history.rows;
    renderIndicatorCharts(allHistoryRows);
    renderComparisonCharts(forecast);
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
      `<p class="error">${error.message}</p>`;
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

loadDashboard();
