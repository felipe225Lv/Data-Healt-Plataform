import { formatDate, formatPct, healthLevel, ruleLabel, statusLabel } from "./lib/format.js";

const API = "/api/v1";
const $ = (id) => document.getElementById(id);
let token = sessionStorage.getItem("dhp-token");

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ?? `Error ${res.status}`);
  return data;
}

function cell(text, className) {
  const td = document.createElement("td");
  td.textContent = text;
  if (className) td.className = className;
  return td;
}

function renderSources(sources) {
  const body = $("sources-body");
  body.replaceChildren();
  for (const s of sources) {
    const tr = document.createElement("tr");
    tr.append(
      cell(s.name), cell(s.type), cell(s.datasets), cell(s.rules),
      cell(formatPct(s.compliance_pct), `nivel ${healthLevel(s.compliance_pct)}`),
      cell(s.open_incidents),
    );
    body.append(tr);
  }
}

function renderRules(rules, canRun) {
  const body = $("rules-body");
  body.replaceChildren();
  for (const r of rules) {
    const tr = document.createElement("tr");
    const action = document.createElement("td");
    if (canRun) {
      const btn = document.createElement("button");
      btn.textContent = "Ejecutar";
      btn.className = "small";
      btn.onclick = async () => {
        await api(`/rules/${r.id}/run`, { method: "POST" });
        await loadDashboard();
      };
      action.append(btn);
    }
    tr.append(
      cell(ruleLabel(r)), cell(`${r.threshold} %`), cell(formatPct(r.last_value)),
      cell(statusLabel(r.last_status), r.last_status === "PASSED" ? "ok" : "mal"), action,
    );
    body.append(tr);
  }
}

function renderIncidents(incidents) {
  const body = $("incidents-body");
  body.replaceChildren();
  if (incidents.length === 0) {
    const tr = document.createElement("tr");
    tr.append(cell("No hay incidentes registrados"));
    body.append(tr);
    return;
  }
  for (const i of incidents) {
    const tr = document.createElement("tr");
    tr.append(
      cell(i.id), cell(i.dataset_name), cell(i.type), cell(formatDate(i.detected_at)),
      cell(statusLabel(i.status)), cell(i.detail),
    );
    body.append(tr);
  }
}

async function loadDashboard() {
  const me = await api("/auth/me");
  $("user-info").textContent = `${me.full_name} (${me.role})`;
  const summary = await api("/dashboard/summary");
  $("kpi-validations").textContent = summary.total_validations;
  $("kpi-incidents").textContent = summary.open_incidents;
  $("kpi-sources").textContent = summary.sources.length;
  renderSources(summary.sources);
  const incidents = await api("/incidents");
  renderIncidents(incidents);
  if (me.role !== "NEGOCIO") {
    renderRules(await api("/rules"), true);
  } else {
    renderRules([], false);
  }
}

function show(loggedIn) {
  $("login-view").hidden = loggedIn;
  $("dashboard-view").hidden = !loggedIn;
  $("logout").hidden = !loggedIn;
}

$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  $("login-error").textContent = "";
  try {
    const res = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
    });
    token = res.access_token;
    sessionStorage.setItem("dhp-token", token);
    show(true);
    await loadDashboard();
  } catch (err) {
    $("login-error").textContent = err.message;
  }
});

$("logout").addEventListener("click", () => {
  token = null;
  sessionStorage.removeItem("dhp-token");
  $("user-info").textContent = "";
  show(false);
});

if (token) {
  show(true);
  loadDashboard().catch(() => show(false));
}
