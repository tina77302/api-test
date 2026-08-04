(() => {
  const pct = (value) => `${(Number(value) * 100).toFixed(1)}%`;
  const number = (value, digits = 2) => Number(value).toFixed(digits);
  const names = { current_rate: "한국 기준금리", inflation: "소비자물가", exchange_rate: "원·달러 환율", bond_3y: "국고채 3년물", us_policy_rate: "미국 기준금리", korea_us_rate_spread: "한미 금리 차", bond_policy_spread: "채권-정책금리 차", inflation_change_6m: "6개월 물가 변화" };

  function renderProbabilities(probabilities) {
    document.querySelector("#home-probability-bars").innerHTML = ["인하", "동결", "인상"].map((label) => `<div class="home-probability ${label}"><span>${label}</span><i><b style="width:${Number(probabilities[label]) * 100}%"></b></i><strong>${pct(probabilities[label])}</strong></div>`).join("");
  }
  function renderDrivers(forecast, latest, previous) {
    const features = new Map();
    Object.values(forecast.models).forEach((model) => model.top_features.forEach((item) => features.set(item.feature, Math.max(features.get(item.feature) ?? 0, item.importance))));
    const top = [...features.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5);
    const values = { ...latest, korea_us_rate_spread: Number(latest.current_rate) - Number(latest.us_policy_rate), bond_policy_spread: Number(latest.bond_3y) - Number(latest.current_rate), inflation_change_6m: Number(latest.inflation) - Number(previous.inflation) };
    document.querySelector("#home-drivers").innerHTML = top.map(([field, importance], index) => `<article><span>0${index + 1}</span><div><strong>${names[field] ?? field}</strong><small>전체 모델 중요도 ${importance.toFixed(3)}</small></div><b>${Number(values[field] ?? 0).toFixed(field === "exchange_rate" ? 1 : 2)}</b></article>`).join("");
  }
  function renderIndicators(rows) {
    const latest = rows.at(-1); const previous = rows.at(-2) ?? latest;
    const items = [["한국 기준금리","current_rate","%"],["소비자물가","inflation","%"],["원·달러 환율","exchange_rate","원"],["국고채 3년물","bond_3y","%"],["미국 기준금리","us_policy_rate","%"],["한미 금리 차","spread","%p"]];
    document.querySelector("#home-indicators").innerHTML = items.map(([label, field, unit]) => { const value = field === "spread" ? Number(latest.current_rate)-Number(latest.us_policy_rate) : Number(latest[field]); const old = field === "spread" ? Number(previous.current_rate)-Number(previous.us_policy_rate) : Number(previous[field]); const change=value-old; return `<article><span>${label}</span><strong>${number(value,field === "exchange_rate" ? 1 : 2)}${unit}</strong><small>${latest.date} · 전월 대비 ${change>0?"상승":change<0?"하락":"변화 없음"}</small></article>`; }).join("");
  }
  function renderHistory(payload) {
    const records = payload.records.slice(-3).reverse();
    document.querySelector("#home-history-preview").innerHTML = records.map((record) => `<article><span>${record.date}</span><strong>${record.prediction} · ${pct(record.probability)}</strong><small>${payload.data_status === "sample" ? "Demo" : record.current ? "Live" : "History"} · ${record.actual ?? "발표 전"} · ${record.correct === null ? "평가 대기" : record.correct ? "적중" : "불일치"}</small></article>`).join("") + (payload.data_status === "sample" ? '<p class="demo-notice">실제 예측 기록이 아닌 UI 확인용 데모 데이터입니다.</p>' : "");
  }
  async function init() {
    try {
      const [forecastResponse, historyResponse, statusResponse, reviewResponse] = await Promise.all([fetch("/forecast/latest"),fetch("/forecast/history?months=12"),fetch("/forecast/status"),fetch("/prediction-history")]);
      if (![forecastResponse,historyResponse,statusResponse,reviewResponse].every((response)=>response.ok)) throw new Error("데이터 연결 실패");
      const forecast=await forecastResponse.json(), history=await historyResponse.json(), status=await statusResponse.json(), review=await reviewResponse.json();
      const ensemble=forecast.latest_ensemble, probabilities=ensemble.probabilities, winning=probabilities[ensemble.direction], latest=history.rows.at(-1), previous=history.rows.at(-7) ?? history.rows[0];
      document.querySelector("#home-direction").textContent=ensemble.direction; document.querySelector("#home-winning-probability").textContent=pct(winning); document.querySelector("#home-current-rate").textContent=`${number(latest.current_rate)}%`; document.querySelector("#home-as-of").textContent=forecast.analysis_period.latest_input; document.querySelector("#home-data-date").textContent=forecast.analysis_period.latest_input; document.querySelector("#home-update-state").textContent=status.automation?.state === "success" ? "자동 업데이트 완료" : "업데이트 상태 확인 필요";
      const ranking=Object.values(probabilities).sort((a,b)=>b-a); document.querySelector("#home-confidence").textContent=ranking[0]-ranking[1] < .15 ? "높은 불확실성" : "보통 불확실성";
      renderProbabilities(probabilities); renderDrivers(forecast,latest,previous); renderIndicators(history.rows); renderHistory(review);
    } catch (error) { document.querySelector("#home-update-state").textContent=error.message; }
  }
  init();
})();
