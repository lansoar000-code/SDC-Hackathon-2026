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
  return ({ demo: "SIMULATED", baseline: "BASELINE", model: "MODEL", mixed: "MIXED" })[source] || source;
}

