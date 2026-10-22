/** DOM 小工具：业务文字只作为文本显示。 */
export function element(tag, text = "", className = "") {
  const node = document.createElement(tag);
  node.textContent = text;
  node.className = className;
  return node;
}

export function setStatus(selector, message, error = false) {
  const node = document.querySelector(selector);
  node.textContent = message;
  node.classList.toggle("is-error", error);
}

export function sourceLabel(source) {
  return ({ demo: "SIMULATED / 模拟", baseline: "BASELINE / 历史基线", model: "MODEL / 训练模型", mixed: "MIXED / 模型与基线" })[source] || source;
}
