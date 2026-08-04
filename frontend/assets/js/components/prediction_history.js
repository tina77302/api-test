(() => {
  const state = { records: [], sortKey: "date", sortDirection: "desc", lastFocus: null };
  const percent = (value) => `${(Number(value) * 100).toFixed(0)}%`;
  const improvements = [
    ["SHAP 기반 예측 설명", "개별 예측에서 각 변수가 방향 확률을 얼마나 높이거나 낮췄는지 계산합니다."],
    ["한국은행 총재 발언 분석", "공식 발언의 물가·성장·금융안정 기조를 텍스트 데이터로 변환합니다."],
    ["금융통화위원회 의사록 분석", "위원별 위험 인식과 정책 성향의 변화를 시계열로 추적합니다."],
    ["뉴스 감성 분석", "경제 뉴스에서 긴축·완화 신호와 시장 불안 수준을 측정합니다."],
    ["시장 기대", "채권금리와 파생시장에 반영된 향후 정책금리 기대를 결합합니다."],
    ["Prediction Confidence Calibration", "모델의 70% 예측이 실제로도 약 70% 맞도록 확률을 보정합니다."],
  ];

  function evaluatedRecords() {
    return state.records.filter((record) => record.actual !== null && record.correct !== null);
  }

  function renderSummary() {
    const evaluated = evaluatedRecords();
    const correct = evaluated.filter((record) => record.correct).length;
    const average = state.records.reduce((sum, record) => sum + Number(record.probability), 0) / Math.max(1, state.records.length);
    const modelScores = new Map();
    evaluated.forEach((record) => {
      const score = modelScores.get(record.model) ?? { correct: 0, count: 0 };
      score.count += 1;
      score.correct += Number(record.correct);
      modelScores.set(record.model, score);
    });
    const bestModel = [...modelScores.entries()].sort((a, b) =>
      b[1].correct / b[1].count - a[1].correct / a[1].count,
    )[0]?.[0] ?? "평가 전";
    const summary = [
      ["Overall Accuracy", evaluated.length ? percent(correct / evaluated.length) : "—"],
      ["Prediction Count", `${state.records.length}건`],
      ["Correct Prediction", `${correct}건`],
      ["Average Confidence", percent(average)],
      ["Best Model", bestModel],
    ];
    document.querySelector("#prediction-summary").innerHTML = summary.map(([label, value]) =>
      `<article><span>${label}</span><strong>${value}</strong></article>`,
    ).join("");
  }

  function renderTimeline() {
    const records = [...state.records].sort((a, b) => a.date.localeCompare(b.date));
    document.querySelector("#prediction-timeline").innerHTML = records.map((record) =>
      `<button type="button" data-history-id="${record.id}" class="${record.current ? "current" : record.correct ? "correct" : "incorrect"}">
        <i></i><span>${record.date}</span><strong>${record.current ? "Current" : record.prediction}</strong>
      </button>`,
    ).join("");
  }

  function sortedRecords() {
    const records = [...state.records];
    const key = state.sortKey;
    records.sort((a, b) => {
      const left = a[key] ?? "";
      const right = b[key] ?? "";
      const compared = typeof left === "number" || typeof left === "boolean"
        ? Number(left) - Number(right)
        : String(left).localeCompare(String(right), "ko");
      return state.sortDirection === "asc" ? compared : -compared;
    });
    return records;
  }

  function resultBadge(record) {
    if (record.actual === null) return '<span class="history-result pending">평가 대기</span>';
    return `<span class="history-result ${record.correct ? "correct" : "incorrect"}">${record.correct ? "정답" : "오답"}</span>`;
  }

  function renderTable() {
    document.querySelector("#prediction-history-body").innerHTML = sortedRecords().map((record) =>
      `<tr tabindex="0" role="button" data-history-id="${record.id}" aria-label="${record.date} 예측 상세 보기">
        <td><strong>${record.date}</strong>${record.current ? '<small class="current-label">CURRENT</small>' : ""}</td>
        <td><span class="direction-chip ${record.prediction}">${record.prediction}</span></td>
        <td>${percent(record.probability)}</td>
        <td>${record.actual ?? "발표 전"}</td>
        <td>${resultBadge(record)}</td>
      </tr>`,
    ).join("");
  }

  function openDetail(record, trigger) {
    state.lastFocus = trigger;
    const maximum = Math.max(...record.featureImportance.map((item) => item.importance));
    const features = record.featureImportance.map((item) =>
      `<div class="history-feature"><div><span>${item.name}</span><strong>${item.direction === "up" ? "상승 신호" : "하락 신호"}</strong></div><i><b style="width:${item.importance / maximum * 100}%"></b></i><small>${percent(item.importance)}</small></div>`,
    ).join("");
    document.querySelector("#prediction-detail-content").innerHTML = `
      <section class="detail-prediction"><div><span>AI Prediction</span><strong>${record.prediction}</strong></div><dl><div><dt>예측 확률</dt><dd>${percent(record.probability)}</dd></div><div><dt>모델 신뢰도</dt><dd>${record.confidence}</dd></div><div><dt>사용 모델</dt><dd>${record.model}</dd></div><div><dt>실제 결정</dt><dd>${record.actual ?? "발표 전"}</dd></div></dl></section>
      <section><h3>Why did AI predict this?</h3><p>${record.reason}</p><div class="history-features">${features}</div></section>
      <section><h3>Why was the actual decision different?</h3><p>${record.actualReason}</p><div class="policy-factor-list">${record.policyFactors.map((factor) => `<span>${factor}</span>`).join("")}</div></section>
      <p class="sample-detail-note">이 상세 설명은 현재 샘플 데이터입니다. 실제 예측 저장 기능과 정책 결정 분석 데이터로 교체할 수 있습니다.</p>`;
    const drawer = document.querySelector("#prediction-detail");
    drawer.classList.add("open");
    drawer.setAttribute("aria-hidden", "false");
    document.body.classList.add("drawer-open");
    document.querySelector("#prediction-detail-close").focus();
  }

  function closeDetail() {
    const drawer = document.querySelector("#prediction-detail");
    drawer.classList.remove("open");
    drawer.setAttribute("aria-hidden", "true");
    document.body.classList.remove("drawer-open");
    state.lastFocus?.focus();
  }

  function activateRecord(event) {
    const trigger = event.target.closest("[data-history-id]");
    if (!trigger) return;
    const record = state.records.find((item) => item.id === trigger.dataset.historyId);
    if (record) openDetail(record, trigger);
  }

  async function initialize() {
    document.querySelector("#future-improvement-cards").innerHTML = improvements.map(([title, description], index) =>
      `<article><span>${String(index + 1).padStart(2, "0")}</span><strong>${title}</strong><p>${description}</p></article>`,
    ).join("");
    try {
      const response = await fetch("/prediction-history");
      if (!response.ok) throw new Error("예측 기록 API 응답 오류");
      const payload = await response.json();
      state.records = payload.records;
      const status = document.querySelector("#history-data-status");
      status.textContent = payload.data_status === "sample" ? "샘플 데이터" : "실제 기록";
      status.classList.toggle("sample", payload.data_status === "sample");
      status.title = payload.description;
      renderSummary();
      renderTimeline();
      renderTable();
    } catch (error) {
      document.querySelector("#prediction-history-body").innerHTML = `<tr><td colspan="5" class="error">${error.message}</td></tr>`;
      document.querySelector("#history-data-status").textContent = "연결 실패";
    }
  }

  document.querySelector(".prediction-table thead").addEventListener("click", (event) => {
    const button = event.target.closest("[data-history-sort]");
    if (!button) return;
    const key = button.dataset.historySort;
    state.sortDirection = state.sortKey === key && state.sortDirection === "asc" ? "desc" : "asc";
    state.sortKey = key;
    renderTable();
  });
  document.querySelector("#prediction-history-body").addEventListener("click", activateRecord);
  document.querySelector("#prediction-history-body").addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); activateRecord(event); }
  });
  document.querySelector("#prediction-timeline").addEventListener("click", activateRecord);
  document.querySelector("#prediction-detail-close").addEventListener("click", closeDetail);
  document.querySelector("#prediction-detail-backdrop").addEventListener("click", closeDetail);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && document.querySelector("#prediction-detail").classList.contains("open")) closeDetail();
  });
  initialize();
})();
