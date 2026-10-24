/** 页面协调层：收集输入、调用 API、展示状态；不在浏览器内计算预测。 */
import { api, apiUrl, describeError } from "./js/api.js";
import { createHistory } from "./js/history.js";
import { refreshMetrics, showTrainingReport } from "./js/charts.js";
import { element, setStatus, sourceLabel } from "./js/ui.js";
import { englishMessage, dishLabel } from "./js/language.js";

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
  if (importing) message = "Importing your file. Please wait.";
  else if (pendingImport) message = "File selected. Click Import sales before training.";
  else if (!dataStatus) message = "Checking saved data…";
  else if (!ready) message = "Saved " + dataStatus.sales.date_count + " dates; training requires at least " + dataStatus.training.minimum_dates + " dates.";
  else message = "Data ready · " + dataStatus.sales.date_count + " dates available for model comparison.";
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
    (result.data_origin === "synthetic" ? " · SYNTHETIC DATA" : "");
  query("#total-quantity").textContent = result.total_recommended_prep;
  query("#predicted-total").textContent = "Expected sales: " + result.total_predicted_sales + " servings";
  query("#prediction-date").textContent = result.target_date + " · " + result.model_version;
  query("#rule-summary-text").textContent = result.warnings.map(englishMessage).join("\n");
  query("#summary-sales").textContent = result.total_predicted_sales;
  query("#summary-buffer").textContent = result.total_recommended_prep - result.total_predicted_sales;
  const rows = result.items.map((item) => {
    const row = element("div", "", "dish-row");
    const label = element("div", "", "dish-name");
    label.append(element("span", "", "dish-badge"), element("span", dishLabel(item.dish_name), "dish-name-text"));
    label.firstChild.setAttribute("aria-hidden", "true");
    const forecast = element("div", item.predicted_sales_quantity, "dish-quantity");
    const prep = element("div", item.recommended_prep_quantity, "dish-quantity");
    prep.append(element("div", item.algorithm || sourceLabel(item.method), "change-label"));
    row.append(label, forecast, prep);
    return row;
  });
  query("#dish-list").replaceChildren(...rows);
  const link = query("#export-link");
  link.href = apiUrl("/predictions/" + encodeURIComponent(result.prediction_id) + "/export");
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
  setStatus("#service-status", "Connected · " + sales.count + " sales records" +
    (sales.count ? " · " + sales.first_date + " — " + sales.last_date : " · Import sales history or try the demo"));
  const options = dishes.length
    ? dishes.map((dish) => {
        const option = element("option", dishLabel(dish.dish_name));
        option.value = dish.dish_id;
        return option;
      })
    : [element("option", "Import dishes and sales first")];
  if (!dishes.length) options[0].value = "";
  query("#actual-dish").replaceChildren(...options);
  if (dishes.some((dish) => dish.dish_id === selectedDish)) query("#actual-dish").value = selectedDish;
  query("#actual-button").disabled = dishes.length === 0;
}

/** 单个操作只锁定自己的按钮；finally 确保失败后可以重试。 */
async function withBusy(button, status, action) {
  if (button.disabled) return;
  button.disabled = true;
  setStatus(status, "Working…");
  try {
    await action();
  } catch (error) {
    setStatus(status, describeError(error), true);
    if (status === "#prediction-status") query("#result-source").textContent = "PLAN FAILED";
  } finally {
    button.disabled = false;
    updateTrainingAvailability();
  }
}

query("#predict-button").addEventListener("click", () => {
  withBusy(query("#predict-button"), "#prediction-status", async () => {
    for (const selector of ["#target-date", "#prep-buffer"]) {
      if (!query(selector).reportValidity()) throw new Error("Enter a valid forecast date and prep buffer.");
    }
    // 隐藏旧结果，避免把上次成功结果误认成这次失败请求的输出。
    query("#results-content").hidden = true;
    query("#empty-state").hidden = false;
    query("#result-source").textContent = "GENERATING";
    query("#summary-sales").textContent = "—";
    query("#total-quantity").textContent = "—";
    query("#summary-buffer").textContent = "—";
    query("#export-link").hidden = true;
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
    setStatus("#prediction-status", "Prep plan saved.");
    await history.refresh();
    query("#overview").scrollIntoView({ behavior: "smooth" });
  });
});

query("#sales-file").addEventListener("change", () => {
  pendingImport = query("#sales-file").files.length > 0;
  setStatus("#import-status", pendingImport ? "File selected. Click Import sales to save it." : "");
  updateTrainingAvailability();
});

query("#import-form").addEventListener("submit", (event) => {
  event.preventDefault();
  withBusy(query("#import-button"), "#import-status", async () => {
    const file = query("#sales-file").files[0];
    if (!file) throw new Error("Select a CSV or XLSX file.");
    if (!dataStatus) throw new Error("The data service is not connected. Refresh and try again.");
    const limit = dataStatus.import_limits.max_upload_bytes;
    if (file.size > limit) throw new Error("The file must not exceed " + limit / (1024 * 1024) + " MB。");
    const body = new FormData();
    body.append("file", file);
    importing = true;
    query("#sales-file").disabled = true;
    updateTrainingAvailability();
    try {
      const result = await api("/data/import", { method: "POST", body, timeout: 120000 });
      pendingImport = false;
      query("#sales-file").value = "";
      setStatus("#import-status", "Saved " + result.imported_rows + " sales records.");
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
      setStatus("#training-status", "Models compared · Trained through " + result.trained_through);
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
    if (!dish) throw new Error("Import dishes and sales history first.");
    const result = await api("/sales", { method: "POST", json: { records: [{
      date: query("#actual-date").value,
      dish_id: dish.dish_id,
      dish_name: dish.dish_name,
      sales_quantity: Number(query("#actual-quantity").value),
    }]}});
    setStatus("#actual-status", englishMessage(result.message));
    await refreshDataStatus();
    await refreshMetrics();
  });
});

query("#refresh-metrics").addEventListener("click", refreshMetrics);

async function initialize() {
  if (location.protocol === "file:") {
    setStatus("#service-status", "Start run.py and open http://127.0.0.1:8000 to connect to the service.", true);
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

query("#demo-button").addEventListener("click", () => {
  query("#forecast-mode").value = "demo";
  query("#predict-button").click();
});
const navigation = [...document.querySelectorAll(".nav-link")];
navigation.forEach((link) => link.addEventListener("click", () => {
  navigation.forEach((item) => item.classList.toggle("active", item === link));
}));




