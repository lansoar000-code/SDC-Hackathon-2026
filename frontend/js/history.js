/** 记录分页与详情读取；展示结果统一交给页面协调层。 */
import { api, describeError } from "./api.js";
import { element, setStatus, sourceLabel } from "./ui.js";

export function createHistory(onSelect) {
  const list = document.querySelector("#history-list");
  const moreButton = document.querySelector("#more-history");
  const refreshButton = document.querySelector("#refresh-history");
  let offset = 0;
  let busy = false;

  async function load(reset = false) {
    if (busy) return;
    busy = true;
    refreshButton.disabled = moreButton.disabled = true;
    setStatus("#history-status", "Loading / 读取中…");
    try {
      const start = reset ? 0 : offset;
      const result = await api("/predictions?limit=20&offset=" + start);
      if (reset) list.replaceChildren();
      for (const record of result.items) {
        const row = element("div", "", "history-row");
        const label = element("span", record.target_date + " · " + sourceLabel(record.source) +
          " · " + record.total_predicted_sales + " 份预测 / " + record.total_recommended_prep + " 份备餐");
        const button = element("button", "View / 查看");
        button.type = "button";
        button.addEventListener("click", async () => {
          button.disabled = true;
          try {
            const detail = await api("/predictions/" + encodeURIComponent(record.prediction_id));
            onSelect(detail);
            setStatus("#prediction-status", "历史记录 · 保存时间 " + detail.created_at);
            document.querySelector("#results-title").scrollIntoView({ behavior: "smooth" });
          } catch (error) {
            setStatus("#history-status", describeError(error), true);
          } finally {
            button.disabled = false;
          }
        });
        row.append(label, button);
        list.append(row);
      }
      offset = start + result.items.length;
      moreButton.hidden = result.items.length < 20;
      setStatus("#history-status", offset ? "已显示 " + offset + " 条保存记录；包含单独标识的模拟结果。" : "还没有预测记录。");
    } catch (error) {
      setStatus("#history-status", describeError(error), true);
    } finally {
      busy = false;
      refreshButton.disabled = moreButton.disabled = false;
    }
  }
  refreshButton.addEventListener("click", () => load(true));
  moreButton.addEventListener("click", () => load(false));
  return { refresh: () => load(true) };
}

