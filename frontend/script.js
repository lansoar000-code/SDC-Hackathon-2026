/** 页面协调层：收集输入、调用 API、展示状态；不在浏览器内计算预测。 */
import { api, describeError } from "./js/api.js";
import { createHistory } from "./js/history.js";
import { refreshMetrics, showTrainingReport } from "./js/charts.js";
import { element, setStatus, sourceLabel } from "./js/ui.js";

const query = (selector) => document.querySelector(selector);
let dishes = [];
let dataStatus = null;
let pendingImport = false;
let importing = false;
let training = false;

/** 文件选择、导入和训练是三个独立步骤；只按已保存的数据判断训练条件。 */
function updateTrainingAvailability() {
  const ready = dataStatus?.training.ready === true;
  query("#train-button").disabled = !ready || pendingImport || importing || training;
  let message;
  if (importing) message = "正在导入文件，请等待导入完成。";
  else if (pendingImport) message = "文件已选择，尚未导入。请先点击「Import / 导入」。";
  else if (!dataStatus) message = "正在读取已保存的数据…";
  else if (!ready) message = "已保存 " + dataStatus.sales.date_count + " 个日期；训练至少需要 " + dataStatus.training.minimum_dates + " 个日期。";
  else message = "数据已就绪 · " + dataStatus.sales.date_count + " 个日期，可以训练并比较模型。";
  setStatus("#data-readiness", message);
}

function localDate(value) {
  const offset = value.getTimezoneOffset() * 60000;
  return new Date(value.getTime() - offset).toISOString().slice(0, 10);
}

const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
query("#target-date").value = localDate(tomorrow);
query("#actual-date").value = localDate(new Date());
query("#actual-date").max = localDate(new Date());

/** 所有外部文本通过 textContent 写入，菜名不会被当成 HTML。 */
function renderPrediction(result) {
  query("#empty-state").hidden = true;
  query("#results-content").hidden = false;
  query("#result-source").textContent = sourceLabel(result.source) +
    (result.data_origin === "synthetic" ? " · 合成数据" : "");
  query("#total-quantity").textContent = result.total_recommended_prep;
  query("#predicted-total").textContent = "Predicted sales / 预测销量：" + result.total_predicted_sales + " 份";
  query("#prediction-date").textContent = result.target_date + " · " + result.model_version;
  query("#rule-summary-text").textContent = result.warnings.join(" ");
  const rows = result.items.map((item) => {
    const row = element("div", "", "dish-row");
    const label = element("div", item.dish_name, "dish-name");
    const quantities = element("div");
    quantities.append(
      element("div", item.recommended_prep_quantity + " 份备餐", "dish-quantity"),
      element("div", "预测 " + item.predicted_sales_quantity + " 份 · " + (item.algorithm || sourceLabel(item.method)), "change-label"),
    );
    row.append(label, quantities);
    return row;
  });
  query("#dish-list").replaceChildren(...rows);
  const link = query("#export-link");
  link.href = "/api/predictions/" + encodeURIComponent(result.prediction_id) + "/export";
  link.hidden = false;
}

const history = createHistory(renderPrediction);

async function refreshDataStatus() {
  const selectedDish = query("#actual-dish").value;
  const [health, dishData] = await Promise.all([api("/health"), api("/dishes")]);
  dishes = dishData.items;
  const sales = health.sales;
  dataStatus = health;
  updateTrainingAvailability();
  setStatus("#service-status", "Connected / 已连接 · " + sales.count + " 条销量" +
    (sales.count ? " · " + sales.first_date + " — " + sales.last_date : " · 先导入历史数据或选择模拟模式"));
  const options = dishes.length
    ? dishes.map((dish) => {
        const option = element("option", dish.dish_name);
        option.value = dish.dish_id;
        return option;
      })
    : [element("option", "请先导入菜品和销量")];
  if (!dishes.length) options[0].value = "";
  query("#actual-dish").replaceChildren(...options);
  if (dishes.some((dish) => dish.dish_id === selectedDish)) query("#actual-dish").value = selectedDish;
  query("#actual-button").disabled = dishes.length === 0;
}

/** 单个操作只锁定自己的按钮；finally 确保失败后可以重试。 */
async function withBusy(button, status, action) {
  if (button.disabled) return;
  button.disabled = true;
  setStatus(status, "Working / 处理中…");
  try {
    await action();
  } catch (error) {
    setStatus(status, describeError(error), true);
    if (status === "#prediction-status") query("#result-source").textContent = "FAILED / 未生成";
  } finally {
    button.disabled = false;
    updateTrainingAvailability();
  }
}

query("#predict-button").addEventListener("click", () => {
  withBusy(query("#predict-button"), "#prediction-status", async () => {
    for (const selector of ["#target-date", "#prep-buffer"]) {
      if (!query(selector).reportValidity()) throw new Error("请填写有效的预测日期和备餐余量。");
    }
    // 隐藏旧结果，避免把上次成功结果误认成这次失败请求的输出。
    query("#results-content").hidden = true;
    query("#empty-state").hidden = false;
    query("#result-source").textContent = "WAITING";
    const selected = (name) => query('input[name="' + name + '"]:checked').value;
    const result = await api("/predictions", { method: "POST", json: {
      target_date: query("#target-date").value,
      weather: selected("weather"),
      is_exam_week: selected("exam") === "yes",
      has_event: selected("event") === "yes",
      mode: query("#forecast-mode").value,
      prep_buffer_percent: Number(query("#prep-buffer").value),
    }});
    renderPrediction(result);
    setStatus("#prediction-status", "Saved / 已保存预测记录");
    await history.refresh();
  });
});

query("#sales-file").addEventListener("change", () => {
  pendingImport = query("#sales-file").files.length > 0;
  setStatus("#import-status", pendingImport ? "已选择文件，请点击「导入」保存到当前数据库。" : "");
  updateTrainingAvailability();
});

query("#import-form").addEventListener("submit", (event) => {
  event.preventDefault();
  withBusy(query("#import-button"), "#import-status", async () => {
    const file = query("#sales-file").files[0];
    if (!file) throw new Error("请选择 CSV 或 XLSX 文件。");
    if (!dataStatus) throw new Error("尚未连接到数据服务，请刷新后重试。");
    const limit = dataStatus.import_limits.max_upload_bytes;
    if (file.size > limit) throw new Error("文件不能超过 " + limit / (1024 * 1024) + " MB。");
    const body = new FormData();
    body.append("file", file);
    importing = true;
    query("#sales-file").disabled = true;
    updateTrainingAvailability();
    try {
      const result = await api("/data/import", { method: "POST", body, timeout: 120000 });
      pendingImport = false;
      query("#sales-file").value = "";
      setStatus("#import-status", result.message);
      await refreshDataStatus();
      await refreshMetrics();
    } finally {
      importing = false;
      query("#sales-file").disabled = false;
      updateTrainingAvailability();
    }
  });
});

query("#train-button").addEventListener("click", () => {
  withBusy(query("#train-button"), "#training-status", async () => {
    training = true;
    query("#import-button").disabled = true;
    try {
      const result = await api("/models/train", { method: "POST", json: {}, timeout: 120000 });
      showTrainingReport(result);
      setStatus("#training-status", "模型比较完成 · 历史截止 " + result.trained_through);
    } finally {
      training = false;
      query("#import-button").disabled = false;
    }
  });
});

query("#actual-form").addEventListener("submit", (event) => {
  event.preventDefault();
  withBusy(query("#actual-button"), "#actual-status", async () => {
    const dish = dishes.find((item) => item.dish_id === query("#actual-dish").value);
    if (!dish) throw new Error("请先导入菜品和历史销量。");
    const result = await api("/sales", { method: "POST", json: { records: [{
      date: query("#actual-date").value,
      dish_id: dish.dish_id,
      dish_name: dish.dish_name,
      sales_quantity: Number(query("#actual-quantity").value),
    }]}});
    setStatus("#actual-status", result.message);
    await refreshDataStatus();
    await refreshMetrics();
  });
});

query("#refresh-metrics").addEventListener("click", refreshMetrics);

async function initialize() {
  if (location.protocol === "file:") {
    setStatus("#service-status", "请先运行项目根目录的 run.py，然后访问 http://127.0.0.1:8000；直接双击 HTML 无法连接后端。", true);
    return;
  }
  try {
    await refreshDataStatus();
  } catch (error) {
    setStatus("#service-status", describeError(error), true);
  }
  const results = await Promise.allSettled([history.refresh(), refreshMetrics(), api("/models/status")]);
  const model = results[2];
  if (model.status === "fulfilled" && model.value.trained) showTrainingReport(model.value);
}
initialize();
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



