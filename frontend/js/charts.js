/** 训练比较与Forecast反馈：图表同时保留数字表格，便于读取精确数量。 */
import { api, describeError } from "./api.js";
import { element, setStatus } from "./ui.js";
import { englishMessage, dishLabel } from "./language.js";

function table(headers, rows) {
  const wrapper = element("div", "", "table-scroll");
  const node = element("table");
  const head = element("thead");
  const heading = element("tr");
  headers.forEach((header) => heading.append(element("th", header)));
  head.append(heading);
  const body = element("tbody");
  for (const values of rows) {
    const row = element("tr");
    values.forEach((value) => row.append(element("td", value ?? "—")));
    body.append(row);
  }
  node.append(head, body);
  wrapper.append(node);
  return wrapper;
}

export function showTrainingReport(artifact) {
  const target = document.querySelector("#training-report");
  target.replaceChildren(
    element("p", "Trained through " + artifact.trained_through + " · Validation from " + artifact.validation_from),
    table(["Dish ID", "Selected model", "XGBoost MAE", "Ridge MAE", "Baseline MAE"], artifact.reports.map((row) => [
      row.dish_id, row.selected, row.xgboost?.mae, row.ridge?.mae, row.baseline?.mae,
    ])),
    element("p", englishMessage(artifact.evaluation_note)),
  );
}

function comparisonChart(rows) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  const samples = rows.slice(-12);
  const height = 46 * samples.length + 36;
  svg.setAttribute("viewBox", "0 0 760 " + height);
  svg.setAttribute("class", "comparison-bars");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Up to twelve recent comparisons: green is actual sales, orange is forecast sales. Exact values are listed below.");
  const maximum = Math.max(1, ...samples.flatMap((row) => [row.actual, row.predicted]));
  function draw(tag, attributes, text = "") {
    const node = document.createElementNS(svg.namespaceURI, tag);
    Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
    node.textContent = text;
    svg.append(node);
  }
  draw("text", { x: 5, y: 18, fill: "#2e654d", "font-size": 13 }, "Actual");
  draw("text", { x: 150, y: 18, fill: "#b95e39", "font-size": 13 }, "Forecast");
  samples.forEach((row, index) => {
    const y = 34 + index * 46;
    draw("text", { x: 0, y: y + 17, fill: "#657469", "font-size": 12 }, row.date + " " + dishLabel(row.dish_name).slice(0, 16));
    draw("rect", { x: 260, y, width: 470 * row.actual / maximum, height: 12, fill: "#2e654d" });
    draw("rect", { x: 260, y: y + 16, width: 470 * row.predicted / maximum, height: 12, fill: "#b95e39" });
  });
  return svg;
}

let loading = false;
export async function refreshMetrics() {
  if (loading) return;
  loading = true;
  const button = document.querySelector("#refresh-metrics");
  button.disabled = true;
  setStatus("#metrics-status", "Loading…");
  try {
    const result = await api("/reports/metrics");
    renderDemandTrend(result.comparisons);
    const metrics = result.metrics;
    const display = (value) => value === null ? "—" : value;
    document.querySelector("#metrics-summary").replaceChildren(
      element("p", "Advance forecast comparisons: " + metrics.count + " · MAE " + display(metrics.mae) +
        " servings · WAPE " + display(metrics.wape_percent) + "% · Bias " + display(metrics.bias)),
      element("p", englishMessage(result.note)),
    );
    const chart = document.querySelector("#comparison-chart");
    chart.replaceChildren();
    if (result.comparisons.length) {
      chart.append(
        comparisonChart(result.comparisons),
        table(["Date", "Dish", "Actual", "Forecast", "Type"], result.comparisons.map((row) => [
          row.date, dishLabel(row.dish_name), row.actual, row.predicted, row.retrospective ? "Retrospective" : "Advance",
        ])),
      );
      setStatus("#metrics-status", "Simulated results are excluded from performance metrics.");
    } else {
      setStatus("#metrics-status", "No actual sales and historical forecasts match the same date and dish yet.");
    }
  } catch (error) {
    setStatus("#metrics-status", describeError(error), true);
  } finally {
    loading = false;
    button.disabled = false;
  }
}


function renderDemandTrend(rows) {
  const target = document.querySelector("#demand-trend");
  if (!rows.length) {
    target.classList.add("trend-empty");
    target.replaceChildren(element("span", "No matched sales yet"), element("p", "Save actual sales for a forecast date to see your demand trend."));
    return;
  }
  const byDate = new Map();
  rows.forEach((row) => {
    const point = byDate.get(row.date) || { date: row.date, actual: 0, predicted: 0 };
    point.actual += row.actual;
    point.predicted += row.predicted;
    byDate.set(row.date, point);
  });
  const points = [...byDate.values()].sort((a, b) => a.date.localeCompare(b.date)).slice(-7);
  const maximum = Math.max(5, ...points.flatMap((p) => [p.actual, p.predicted]));
  const ceiling = Math.ceil(maximum / 5) * 5;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 500 230");
  svg.setAttribute("class", "demand-chart");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Actual and forecast servings for matched dishes, by date. Exact values are shown in Forecast performance.");
  const draw = (tag, attributes, text = "") => {
    const node = document.createElementNS(svg.namespaceURI, tag);
    Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
    node.textContent = text;
    svg.append(node);
    return node;
  };
  const x = (i) => points.length === 1 ? 267 : 46 + i * 434 / (points.length - 1);
  const y = (value) => 191 - value / ceiling * 166;
  for (let tick = 0; tick <= 4; tick++) {
    const value = Math.round(ceiling * tick / 4);
    draw("line", { x1: 46, y1: y(value), x2: 480, y2: y(value), stroke: "#e4e0d6", "stroke-dasharray": "3 3" });
    draw("text", { x: 35, y: y(value) + 4, fill: "#7b8278", "font-size": 11, "text-anchor": "end" }, value);
  }
  points.forEach((point, i) => {
    draw("line", { x1: x(i), y1: 25, x2: x(i), y2: 191, stroke: "#e4e0d6", "stroke-dasharray": "3 3" });
    draw("text", { x: x(i), y: 216, fill: "#7b8278", "font-size": 10, "text-anchor": "middle" }, point.date.slice(5));
  });
  [["actual", "#2e654d"], ["predicted", "#b95e39"]].forEach(([key, color]) => {
    draw("polyline", { points: points.map((point, i) => x(i) + "," + y(point[key])).join(" "), fill: "none", stroke: color, "stroke-width": 1.8, ...(key === "predicted" ? { "stroke-dasharray": "6 5" } : {}) });
    points.forEach((point, i) => {
      const circle = draw("circle", { cx: x(i), cy: y(point[key]), r: 3.2, fill: color });
      const title = document.createElementNS(svg.namespaceURI, "title");
      title.textContent = point.date + " · " + key + ": " + point[key] + " servings";
      circle.append(title);
    });
  });
  target.classList.remove("trend-empty");
  target.replaceChildren(svg);
}


