(() => {
  const events = [
    {
      id: "global-financial-crisis", title: "글로벌 금융위기", shortTitle: "금융위기",
      startDate: "2008-09", endDate: "2009-06", category: "financial-crisis",
      summary: "글로벌 신용 경색과 실물경제 위축이 동시에 진행된 금융 시스템 충격 구간입니다.",
      koreaResponse: "한국은행은 경기와 금융시장 안정을 위해 기준금리를 빠르게 인하하고 유동성 공급 조치를 병행했습니다.",
      usResponse: "연준은 정책금리를 사실상 제로 수준으로 낮추고 비전통적 자산매입 정책을 확대했습니다.",
      economicImpact: ["글로벌 신용 경색", "성장·물가 압력 약화", "안전자산 선호와 환율 변동성 확대"],
      modelImpact: "평상시보다 정책 대응 속도와 금융시장 스트레스의 영향이 커지는 구조적 변화 구간입니다.",
      reflectedFeatures: ["환율", "국고채 3년물", "미국 기준금리", "한미 금리 차"],
      missingInformation: ["금융기관 건전성", "신용 스프레드", "비상 유동성 정책"],
      improvement: "금융 스트레스 지표와 위기 국면 탐지, 스트레스 테스트를 결합할 수 있습니다.",
      learnPath: "/learn?topic=구조적%20변화", sourceNote: "기간은 기존 RateScope 차트의 금융위기 Annotation 범위를 유지했습니다."
    },
    {
      id: "covid-19-pandemic", title: "코로나19 팬데믹", shortTitle: "코로나19",
      startDate: "2020-02", endDate: "2021-12", category: "pandemic",
      summary: "이동 제한과 생산 차질, 대규모 정책 대응이 동시에 발생해 일반적인 경기 순환 관계가 흔들린 기간입니다.",
      koreaResponse: "한국은행은 충격 초기에 금리를 낮추고 금융시장 안정 조치를 시행한 뒤 회복과 금융불균형을 보며 정상화를 시작했습니다.",
      usResponse: "연준은 제로금리와 대규모 자산매입으로 대응했고 회복 이후 긴축 전환을 준비했습니다.",
      economicImpact: ["경제활동 급감", "공급망 병목", "초기 디플레이션 압력 이후 물가 상승"],
      modelImpact: "학습 데이터에서 드문 보건 충격이며 변수 관계가 빠르게 바뀌어 과거 패턴 기반 모델의 불확실성이 커집니다.",
      reflectedFeatures: ["물가", "실업률", "환율", "한국·미국 기준금리"],
      missingInformation: ["이동 제한", "감염 확산", "재정지원", "중앙은행 비정상 정책"],
      improvement: "이상 탐지, 국면별 모델과 뉴스·정책 문서 분석을 결합할 수 있습니다.",
      learnPath: "/learn?topic=블랙%20스완", sourceNote: "시작은 프로젝트 월별 데이터에서 팬데믹 충격이 관측되는 2020-02, 종료는 기존 Annotation 범위인 2021-12입니다."
    },
    {
      id: "global-inflation-surge", title: "글로벌 인플레이션 급등", shortTitle: "인플레이션",
      startDate: "2021-01", endDate: "2022-12", category: "inflation",
      summary: "공급 제약과 수요 회복이 겹치며 물가상승률이 빠르게 높아지고 통화정책의 중심이 물가 안정으로 이동한 구간입니다.",
      koreaResponse: "한국은행은 물가 압력과 금융불균형을 함께 고려하며 완화 정도를 축소했습니다.",
      usResponse: "연준은 높은 인플레이션이 지속되자 자산매입을 종료하고 빠른 긴축으로 전환했습니다.",
      economicImpact: ["소비자물가 상승", "시장금리 상승", "실질구매력 약화와 성장 우려"],
      modelImpact: "물가 수준뿐 아니라 상승 속도와 정책 반응의 시차가 중요해지는 구간입니다.",
      reflectedFeatures: ["물가", "1·3·6개월 물가 변화", "국고채 금리"],
      missingInformation: ["공급망 병목 지수", "기대인플레이션", "에너지·원자재 충격"],
      improvement: "기대인플레이션과 공급망·원자재 변수를 시차 Feature로 추가할 수 있습니다.",
      learnPath: "/learn?topic=데이터%20드리프트", sourceNote: "2021~2022년을 프로젝트의 월별 물가 가속과 긴축 전환을 설명하는 학습 구간으로 정의했습니다."
    },
    {
      id: "policy-tightening-cycle", title: "주요 금리 인상기", shortTitle: "긴축 전환",
      startDate: "2021-08", endDate: "2023-01", category: "policy-shift",
      summary: "한국 기준금리가 인상 방향으로 전환되고 연준도 뒤이어 빠른 긴축에 나서며 한·미 정책 경로가 크게 움직인 기간입니다.",
      koreaResponse: "한국은행은 2021년 8월부터 기준금리 정상화를 시작해 물가와 금융불균형에 대응했습니다.",
      usResponse: "연준은 2022년 금리 인상을 시작해 높은 물가에 대응하는 빠른 긴축을 진행했습니다.",
      economicImpact: ["정책금리와 채권금리 상승", "한미 금리 차 변화", "환율과 자금조달 비용 변동"],
      modelImpact: "직전 금리 방향과 금리 차 Feature가 강하게 작동할 수 있지만 정책 속도 변화는 과거 평균과 다를 수 있습니다.",
      reflectedFeatures: ["최근 3개월 금리 방향", "한미 금리 차", "채권-정책금리 차"],
      missingInformation: ["정책위원 발언", "시장 기대금리", "회의별 의결문 변화"],
      improvement: "의사록·총재 발언과 시장 기대금리를 결합해 정책 전환 시점을 보완할 수 있습니다.",
      learnPath: "/learn?topic=예측%20확률", sourceNote: "한국은행 기준금리 인상 전환부터 프로젝트 기존 급격한 인상 Annotation 종료까지의 범위입니다."
    }
  ];
  const categories = {
    "financial-crisis": {label:"금융위기", tone:"crisis", marker:"◆"},
    pandemic: {label:"팬데믹", tone:"pandemic", marker:"●"},
    inflation: {label:"인플레이션", tone:"inflation", marker:"▲"},
    recovery: {label:"경기회복", tone:"recovery", marker:"■"},
    "policy-shift": {label:"정책 전환", tone:"policy-shift", marker:"◇"},
    geopolitical: {label:"지정학", tone:"geopolitical", marker:"✦"}
  };
  window.RateScopeEconomicEvents = Object.freeze({events:Object.freeze(events),categories:Object.freeze(categories)});
})();
