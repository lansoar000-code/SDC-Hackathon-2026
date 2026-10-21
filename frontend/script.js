const predictionRules = {
  friedRice: {
    name: "Fried rice",
    emoji: "🍳",
    base: 80,
    weather: { sunny: 5, cloudy: 0, rainy: -10 },
    exam: 15,
    event: 25,
  },
  noodles: {
    name: "Noodles",
    emoji: "🍜",
    base: 65,
    weather: { sunny: 0, cloudy: 5, rainy: 10 },
    exam: 10,
    event: 20,
  },
  chickenRice: {
    name: "Chicken rice",
    emoji: "🍗",
    base: 70,
    weather: { sunny: 10, cloudy: 5, rainy: -5 },
    exam: 20,
    event: 30,
  },
};

const weatherLabels = {
  sunny: "sunny weather",
  cloudy: "cloudy weather",
  rainy: "rainy weather",
};

const predictButton = document.querySelector("#predict-button");
const emptyState = document.querySelector("#empty-state");
const resultsContent = document.querySelector("#results-content");
const dishList = document.querySelector("#dish-list");
const totalQuantity = document.querySelector("#total-quantity");
const ruleSummaryText = document.querySelector("#rule-summary-text");

function getSelectedValue(name) {
  return document.querySelector(`input[name="${name}"]:checked`).value;
}

function estimateDish(rule, weather, isExamWeek, hasEvent) {
  const percentChange =
    rule.weather[weather] +
    (isExamWeek ? rule.exam : 0) +
    (hasEvent ? rule.event : 0);

  return {
    ...rule,
    percentChange,
    quantity: Math.max(0, Math.round(rule.base * (1 + percentChange / 100))),
  };
}

function formatChange(percent) {
  if (percent === 0) return "baseline";
  return `${percent > 0 ? "+" : ""}${percent}% vs. baseline`;
}

function renderPrediction() {
  const weather = getSelectedValue("weather");
  const isExamWeek = getSelectedValue("exam") === "yes";
  const hasEvent = getSelectedValue("event") === "yes";

  const dishes = Object.values(predictionRules).map((rule) =>
    estimateDish(rule, weather, isExamWeek, hasEvent),
  );

  dishList.innerHTML = dishes
    .map(
      (dish) => `
        <div class="dish-row">
          <div class="dish-name">
            <span class="dish-emoji" aria-hidden="true">${dish.emoji}</span>
            <span>${dish.name}</span>
          </div>
          <div>
            <div class="dish-quantity">${dish.quantity}<span>servings</span></div>
            <div class="change-label">${formatChange(dish.percentChange)}</div>
          </div>
        </div>
      `,
    )
    .join("");

  totalQuantity.textContent = dishes.reduce((total, dish) => total + dish.quantity, 0);

  const context = [weatherLabels[weather]];
  if (isExamWeek) context.push("exam week");
  if (hasEvent) context.push("a local event");

  ruleSummaryText.textContent =
    `Sample rule: each dish starts from a demo baseline, then adjusts for ${context.join(", ")}. ` +
    "This estimate is illustrative, not a real demand forecast.";

  emptyState.hidden = true;
  resultsContent.hidden = false;
}

predictButton.addEventListener("click", renderPrediction);

