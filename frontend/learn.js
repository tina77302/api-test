(() => {
  const basic = [
    ["기준금리란?","중앙은행이 물가와 금융안정을 위해 운용하는 정책금리입니다. 예금·대출·채권금리의 기준점 역할을 합니다."],
    ["금리가 오르면 어떤 일이 발생하는가?","대출 부담과 저축 유인이 커져 소비·투자가 둔화될 수 있고, 수요 압력이 줄어 물가 안정에 도움이 될 수 있습니다."],
    ["금리가 내리면 어떤 일이 발생하는가?","자금 조달 비용이 낮아져 소비·투자를 지원하지만, 환율·부채·자산가격 위험을 키울 수도 있습니다."],
    ["CPI란?","소비자물가지수로 가계가 구입하는 상품과 서비스 가격의 변화를 측정합니다. 금리 판단에서 물가 압력을 보는 핵심 지표입니다."],
    ["GDP란?","일정 기간 생산된 최종 재화와 서비스의 가치입니다. 성장 둔화는 완화 필요성을, 과열은 긴축 필요성을 높일 수 있습니다."],
    ["실업률이 금리에 미치는 영향","실업률 상승은 경기 약화 신호가 될 수 있어 인하 압력을 높이지만, 물가와 금융안정 상황을 함께 봐야 합니다."],
    ["환율이 금리에 미치는 영향","원화 약세는 수입물가와 자금 유출 부담을 높여 금리 인하를 제약할 수 있습니다."],
    ["미국 CPI가 한국 금리에 영향을 주는 과정","미국 물가 → 연준 정책금리 기대 → 달러와 글로벌 자금 흐름 → 원·달러 환율과 한미 금리 차 → 한국 정책 여건으로 연결됩니다."],
    ["한미 기준금리 차의 의미","한국 금리에서 미국 금리를 뺀 값입니다. 격차 자체보다 환율, 자본 흐름과 각국 경기 상황을 함께 해석해야 합니다."],
  ];
  const calculations = [
    ["CPI 전년 동월 대비 계산","(현재 CPI ÷ 12개월 전 CPI − 1) × 100","현재 120, 전년 116이면 (120÷116−1)×100 = 3.45%"],
    ["CPI 전월 대비 계산","(현재 CPI ÷ 전월 CPI − 1) × 100","현재 120, 전월 119.5이면 0.42%"],
    ["환율 변화율 계산","(현재 환율 ÷ 과거 환율 − 1) × 100","1,450원에서 1,500원이면 3.45% 상승"],
    ["한미 기준금리 차 계산","한국 기준금리 − 미국 기준금리","한국 3.50%, 미국 5.25%이면 −1.75%p"],
    ["금리 변화량 계산","현재 기준금리 − 과거 기준금리","3.50%에서 3.25%가 되면 −0.25%p"],
    ["1개월·3개월·6개월 변화 변수 계산","현재 값 − 각 시차의 과거 값","현재 물가 3.0%, 3개월 전 3.6%이면 3개월 변화는 −0.6%p"],
  ];
  const machine = [
    ["Random Forest란?","서로 다른 표본과 변수를 사용한 여러 의사결정나무의 결과를 평균해 비선형 관계를 학습합니다."],
    ["XGBoost란?","앞선 나무가 틀린 사례를 다음 나무가 순차적으로 보완해 최종 점수를 만드는 부스팅 모델입니다."],
    ["두 모델을 함께 사용하는 이유","학습 방식이 다른 모델의 확률을 결합해 한 모델의 편향과 불안정성을 완화하려는 목적입니다."],
    ["2단계 분류를 사용한 이유","동결이 많은 데이터에서 먼저 변경 여부를 판단하고, 변경 조건에서 인하·인상을 구분해 클래스 불균형을 다룹니다."],
    ["TimeSeriesSplit이란?","과거 구간으로 학습하고 그보다 미래 구간으로 검증하는 시계열 전용 분할입니다."],
    ["Nested Time Series Validation을 사용한 이유","설정을 고르는 내부 검증과 최종 성능을 측정하는 외부 평가를 분리해 과대평가를 줄입니다."],
    ["Feature Importance란?","모델 전체에서 변수가 분할과 오류 감소에 사용된 정도입니다. 개별 예측의 원인이나 인과관계는 아닙니다."],
    ["SHAP이란?","특정 예측에서 각 변수가 기준 예측을 얼마나 올리거나 낮췄는지 일관된 방식으로 배분하는 설명 기법입니다."],
    ["신뢰도와 예측 확률의 차이","예측 확률은 모델 출력이고, 신뢰도는 검증 성능·모델 합의·데이터 품질까지 포함한 더 넓은 판단입니다."],
    ["확률 보정이 필요한 이유","모델이 70%라고 말한 사례가 실제로도 약 70% 맞도록 출력 확률과 실제 빈도를 맞추기 위해 필요합니다."],
  ];
  const risks = [
    ["블랙 스완","과거에 거의 없던 극단적 충격","예상 밖의 거대한 파도","팬데믹·전쟁·금융 시스템 붕괴","유사 학습 사례가 부족하고 변수 관계가 급변합니다.","현재 모델은 발생 자체를 예측하지 못하며 불확실성 경고만 제공합니다.","스트레스 테스트, 이상 탐지와 전문가 규칙을 결합합니다."],
    ["그레이 라이노","알려져 있지만 대응이 늦을 수 있는 큰 위험","멀리서 보이지만 피하지 않는 위험","가계부채·부동산 과열·인구구조 변화","발생 시점과 임계 수준이 불확실합니다.","관련 지표가 현재 Feature에 모두 포함된 것은 아닙니다.","부채·주택·연체율을 시차 Feature로 추가합니다."],
    ["구조적 변화","경제 변수 사이의 관계가 장기적으로 바뀌는 현상","과거의 지도와 현재 길이 달라지는 상황","팬데믹 이후 물가·공급망 변화","과거에 맞던 규칙이 현재에는 틀릴 수 있습니다.","포스트 팬데믹 모델을 별도로 비교합니다.","국면 탐지와 기간별 모델을 운영합니다."],
    ["데이터 드리프트","모델 입력 분포가 학습 당시와 달라지는 현상","익숙하지 않은 범위의 숫자가 들어오는 상황","환율·물가의 장기 레벨 변화","학습 범위 밖에서는 외삽이 불안정합니다.","주요 지표의 과거 범위 이탈을 점검합니다.","드리프트 알림과 재학습 기준을 둡니다."],
    ["스트레스 테스트","극단적 가정을 넣어 모델과 시스템의 반응을 확인하는 방법","사고가 나기 전 비상훈련","환율 20% 상승·물가 재급등 시나리오","시나리오가 실제 미래와 같다는 보장은 없습니다.","현재 정규 예측 파이프라인에는 미포함입니다.","정책 변수별 충격 시나리오를 별도 제공합니다."],
    ["극단적 시나리오 분석","여러 위험이 동시에 발생하는 꼬리 위험을 비교하는 분석","최악·중간·기본 경로를 나란히 보는 방법","전쟁과 공급 충격, 환율 급등의 결합","변수 간 충격 관계를 가정해야 합니다.","현재 단일 최신 입력을 사용합니다.","확률적 시나리오와 민감도 분석을 추가합니다."],
  ];
  const categories = [
    {id:"basic",name:"경제 기초",items:basic.map(([title,body])=>({title,html:`<p>${body}</p><a href="/#current-prediction">현재 전망과 연결해서 보기 →</a>`}))},
    {id:"calculation",name:"경제지표 계산법",items:calculations.map(([title,formula,example])=>({title,html:`<dl class="formula-detail"><div><dt>공식</dt><dd><code>${formula}</code></dd></div><div><dt>숫자 예시</dt><dd>${example}</dd></div></dl><a href="/model#features">관련 변수 보기 →</a>`}))},
    {id:"machine",name:"머신러닝 이해",items:machine.map(([title,body])=>({title,html:`<p>${body}</p><a href="/model#model-classroom">관련 모델 보기 →</a>`}))},
    {id:"risk",name:"경제 리스크",items:risks.map(([title,definition,easy,example,difficulty,current,future])=>({title,html:`<dl class="risk-learning"><div><dt>정의</dt><dd>${definition}</dd></div><div><dt>쉬운 설명</dt><dd>${easy}</dd></div><div><dt>대표 사례</dt><dd>${example}</dd></div><div><dt>AI가 다루기 어려운 이유</dt><dd>${difficulty}</dd></div><div><dt>현재 모델 반영</dt><dd>${current}</dd></div><div><dt>향후 개선</dt><dd>${future}</dd></div></dl><a href="/insight">프로젝트 인사이트 보기 →</a>`}))},
  ];
  let selected="all";
  function render(){const query=document.querySelector("#learn-search").value.trim().toLowerCase();let count=0;document.querySelector("#learn-content").innerHTML=categories.filter(c=>selected==="all"||c.id===selected).map(category=>{const items=category.items.filter(item=>(item.title+item.html).toLowerCase().includes(query));count+=items.length;if(!items.length)return"";return `<section class="learn-category"><header><span>${category.name}</span><strong>${items.length}개 주제</strong></header>${items.map(item=>`<details><summary>${item.title}<span>+</span></summary><div>${item.html}</div></details>`).join("")}</section>`;}).join("");document.querySelector("#learn-result-count").textContent=`${count}개의 학습 주제`;}
  document.querySelector("#learn-filters").innerHTML=[{id:"all",name:"전체"},...categories].map(c=>`<button type="button" data-category="${c.id}" class="${c.id==="all"?"active":""}">${c.name}</button>`).join("");
  document.querySelector("#learn-filters").addEventListener("click",e=>{const b=e.target.closest("[data-category]");if(!b)return;selected=b.dataset.category;document.querySelectorAll("[data-category]").forEach(x=>x.classList.toggle("active",x===b));render();});document.querySelector("#learn-search").addEventListener("input",render);render();
})();
