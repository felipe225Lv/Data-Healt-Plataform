// Funciones puras del dashboard (se prueban con node --test)

export function formatPct(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "Sin datos";
  return `${Number(value).toFixed(1)} %`;
}

export function healthLevel(pct) {
  if (pct === null || pct === undefined) return "sin-datos";
  if (pct >= 95) return "bien";
  if (pct >= 80) return "alerta";
  return "critico";
}

export function statusLabel(status) {
  const labels = {
    PASSED: "Cumple",
    FAILED: "No cumple",
    ERROR: "Error de conexión",
    ABIERTO: "Abierto",
    RESUELTO: "Resuelto",
  };
  return labels[status] ?? status ?? "Sin ejecutar";
}

export function ruleLabel(rule) {
  const tipos = {
    completeness: "Completitud",
    uniqueness: "Unicidad",
    validity: "Validez",
    freshness: "Oportunidad",
    volume: "Volumen",
  };
  const tipo = tipos[rule.rule_type] ?? rule.rule_type;
  return rule.column ? `${tipo} de ${rule.column}` : tipo;
}

export function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
