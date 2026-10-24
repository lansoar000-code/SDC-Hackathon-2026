import { apiUrl } from "./api.js";

// Prototype approval only: no login or real identity is implied.
const anchor = document.querySelector("#export-link");
const bar = document.createElement("div");
bar.style.cssText = "display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-top:12px";
const approve = document.createElement("button");
approve.type = "button";
approve.textContent = "Approve plan";
const status = document.createElement("span");
status.setAttribute("role", "status");
status.setAttribute("aria-live", "polite");
bar.append(approve, status);
anchor.after(bar);
let current = null;
let plan = null;
let busy = false;
let generation = 0;

async function request(path, method = "GET", body) {
  const response = await fetch(apiUrl(path), {
    method,
    headers: { "Content-Type": "application/json", "X-Demo-Actor": "demo-owner" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.error?.message || `Request failed (${response.status})`);
  }
  return response;
}
async function json(path, method, body) { return (await request(path, method, body)).json(); }
function render() {
  const approved = plan?.status === "approved";
  approve.textContent = approved ? "Approved" : "Approve plan";
  approve.disabled = busy || approved || !current;
  if (current) {
    anchor.href = apiUrl(approved ? `/plan-reviews/${plan.review_id}/export` : `/predictions/${current.prediction_id}/export`);
    anchor.textContent = approved ? "Download approved CSV" : "Download prep plan CSV";
  }
  if (approved) status.textContent = `Approved ${new Date(plan.approved_at).toLocaleString()}`;
}
document.addEventListener("prepwise:prediction", async (event) => {
  const token = ++generation;
  current = event.detail;
  plan = null;
  status.textContent = "Checking approval…";
  busy = true;
  render();
  try {
    const result = await json(`/plan-review-status/${encodeURIComponent(current.prediction_id)}`);
    if (token !== generation) return;
    plan = result.review;
    status.textContent = "Pending approval";
  } catch (error) {
    if (token !== generation) return;
    status.textContent = error.message || "Unable to load approval status.";
  } finally {
    if (token === generation) { busy = false; render(); }
  }
});
approve.onclick = async () => {
  if (!current || busy) return;
  const token = generation;
  const predictionId = current.prediction_id;
  busy = true;
  status.textContent = "Approving…";
  render();
  try {
    let result = await json("/plan-reviews", "POST", { prediction_id: predictionId });
    if (result.status !== "approved") result = await json(`/plan-reviews/${result.review_id}/approve`, "POST", { expected_revision: result.revision });
    if (token === generation) { plan = result; status.textContent = "Plan approved."; }
  } catch (error) {
    if (token === generation) status.textContent = error.message || "Approval failed. Please try again.";
  } finally {
    if (token === generation) { busy = false; render(); }
  }
};

render();
