/** 页面协调层：收集输入、调用 API、展示状态；不在浏览器内计算预测。 */
import { api, describeError } from "./js/api.js";
import { createHistory } from "./js/history.js";
import { refreshMetrics, showTrainingReport } from "./js/charts.js";
import { element, setStatus, sourceLabel } from "./js/ui.js";

const query = (selector) => document.querySelector(selector);
let dishes = [];

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

query("#import-form").addEventListener("submit", (event) => {
  event.preventDefault();
  withBusy(query("#import-button"), "#import-status", async () => {
    const file = query("#sales-file").files[0];
    if (!file) throw new Error("请选择 CSV 或 XLSX 文件。");
    if (file.size > 5 * 1024 * 1024) throw new Error("文件不能超过 5 MB。");
    const body = new FormData();
    body.append("file", file);
    const result = await api("/data/import", { method: "POST", body });
    setStatus("#import-status", result.message);
    await refreshDataStatus();
    await refreshMetrics();
  });
});

query("#train-button").addEventListener("click", () => {
  withBusy(query("#train-button"), "#training-status", async () => {
    const result = await api("/models/train", { method: "POST", json: {}, timeout: 120000 });
    showTrainingReport(result);
    setStatus("#training-status", "模型比较完成 · 历史截止 " + result.trained_through);
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


