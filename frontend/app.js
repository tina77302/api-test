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
  document.querySelector("#fold-timeline").innerHTML = Array.from({length: foldCount}, (_, index) => {
    const cells = models.map(([name, model]) => {
      const fold = model.folds[index];
      return `<div><span>${modelNameMap[name]}</span><strong>${percent(fold.metrics.accuracy)}</strong><small>Macro F1 ${Number(fold.metrics.macro_f1).toFixed(3)}</small></div>`;
    }).join("");
    const sample = models[0][1].folds[index];
    return `<article><header><span>FOLD ${String(index + 1).padStart(2, "0")}</span><strong>${sample.train_samples}개월 학습 → ${sample.test_samples}개월 평가</strong></header>${cells}</article>`;
  }).join("");
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
      fetch("/forecast/history?months=36"),
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

    renderHistory(history.rows);
    allHistoryRows = history.rows;
    renderIndicatorCharts(allHistoryRows);
    renderDecisionDrivers(allHistoryRows, forecast);
    renderFoldTimeline(forecast);
    renderWatchList(allHistoryRows);
    renderComparisonCharts(forecast);
    renderAnalysisExplanation(forecast);
    renderReliability(reliability);
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
