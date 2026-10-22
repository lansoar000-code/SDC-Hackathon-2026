/** 同源 API 客户端：统一超时、JSON 与错误处理。 */
export async function api(path, { method = "GET", json, body, timeout = 30000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch("/api" + path, {
      method,
      headers: json === undefined ? {} : { "Content-Type": "application/json" },
      body: json === undefined ? body : JSON.stringify(json),
      signal: controller.signal,
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const error = new Error(data?.error?.message || "请求失败，HTTP " + response.status);
      error.details = data?.error?.details;
      throw error;
    }
    if (data === null) throw new Error("服务返回了无法读取的响应。");
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("请求超时；操作可能仍在服务端处理，请先刷新确认结果后再重试。");
    if (error instanceof TypeError) throw new Error("无法连接服务，请确认 run.py 正在运行。");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function describeError(error) {
  let message = error.message || "操作失败";
  if (error.details) message += "\n" + JSON.stringify(error.details, null, 2);
  return message;
}

