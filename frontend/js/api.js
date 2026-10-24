import { englishMessage } from "./language.js";
export const apiUrl = (path) => "/api" + path;
/** 同源 API 客户端：统一超时、JSON 与错误处理。 */
export async function api(path, { method = "GET", json, body, timeout = 30000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(apiUrl(path), {
      method,
      headers: json === undefined ? {} : { "Content-Type": "application/json" },
      body: json === undefined ? body : JSON.stringify(json),
      signal: controller.signal,
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const error = new Error(englishMessage(data?.error?.message) || "Request failed. HTTP " + response.status);
      error.details = data?.error?.details;
      throw error;
    }
    if (data === null) throw new Error("The service returned an unreadable response.");
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("The request timed out. It may still be processing; refresh before trying again.");
    if (error instanceof TypeError) throw new Error("Cannot connect to the service. Check that the server is running.");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function describeError(error) {
  let message = error.message || "The operation failed.";
  if (error.details) message += "\n" + JSON.stringify(error.details, (key, value) => typeof value === "string" ? englishMessage(value) : value, 2);
  return message;
}


