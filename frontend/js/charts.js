/** 训练比较与预测反馈：图表同时保留数字表格，便于读取精确数量。 */
import { api, describeError } from "./api.js";
import { element, setStatus } from "./ui.js";

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
    element("p", "训练截止 " + artifact.trained_through + "；验证起点 " + artifact.validation_from),
    table(["菜品编号", "选择", "XGBoost MAE", "Ridge MAE", "基线 MAE"], artifact.reports.map((row) => [
      row.dish_id, row.selected, row.xgboost?.mae, row.ridge?.mae, row.baseline?.mae,
    ])),
    element("p", artifact.evaluation_note),
  );
}

function comparisonChart(rows) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  const samples = rows.slice(-12);
  const height = 46 * samples.length + 36;
  svg.setAttribute("viewBox", "0 0 760 " + height);
  svg.setAttribute("class", "comparison-bars");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "最近最多十二条对比：绿色为实际销量，蓝色为预测销量。详细数字见下方表格。");
  const maximum = Math.max(1, ...samples.flatMap((row) => [row.actual, row.predicted]));
  function draw(tag, attributes, text = "") {
    const node = document.createElementNS(svg.namespaceURI, tag);
    Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
    node.textContent = text;
    svg.append(node);
  }
  draw("text", { x: 5, y: 18, fill: "#c8f169", "font-size": 13 }, "Actual / 实际");
  draw("text", { x: 150, y: 18, fill: "#89c5ff", "font-size": 13 }, "Predicted / 预测");
  samples.forEach((row, index) => {
    const y = 34 + index * 46;
    draw("text", { x: 0, y: y + 17, fill: "#dbe3d7", "font-size": 12 }, row.date + " " + row.dish_name.slice(0, 12));
    draw("rect", { x: 260, y, width: 470 * row.actual / maximum, height: 12, fill: "#c8f169" });
    draw("rect", { x: 260, y: y + 16, width: 470 * row.predicted / maximum, height: 12, fill: "#89c5ff" });
  });
  return svg;
}

let loading = false;
export async function refreshMetrics() {
  if (loading) return;
  loading = true;
  const button = document.querySelector("#refresh-metrics");
  button.disabled = true;
  setStatus("#metrics-status", "Loading / 读取中…");
  try {
    const result = await api("/reports/metrics");
    const metrics = result.metrics;
    const display = (value) => value === null ? "—" : value;
    document.querySelector("#metrics-summary").replaceChildren(
      element("p", "事前预测对比样本：" + metrics.count + " · MAE " + display(metrics.mae) +
        " 份 · WAPE " + display(metrics.wape_percent) + "% · Bias " + display(metrics.bias)),
      element("p", result.note),
    );
    const chart = document.querySelector("#comparison-chart");
    chart.replaceChildren();
    if (result.comparisons.length) {
      chart.append(
        comparisonChart(result.comparisons),
        table(["日期", "菜品", "实际", "预测", "类型"], result.comparisons.map((row) => [
          row.date, row.dish_name, row.actual, row.predicted, row.retrospective ? "补做历史预测" : "事前预测",
        ])),
      );
      setStatus("#metrics-status", "模拟结果不进入效果统计。");
    } else {
      setStatus("#metrics-status", "还没有同日期、同菜品的实际销量与历史预测可比较。");
    }
  } catch (error) {
    setStatus("#metrics-status", describeError(error), true);
  } finally {
    loading = false;
    button.disabled = false;
  }
}

