import assert from "node:assert/strict";
import { test } from "node:test";

import { formatPct, healthLevel, ruleLabel, statusLabel } from "../src/lib/format.js";

test("formatPct muestra un decimal y maneja valores vacíos", () => {
  assert.equal(formatPct(80), "80.0 %");
  assert.equal(formatPct(null), "Sin datos");
});

test("healthLevel clasifica el cumplimiento", () => {
  assert.equal(healthLevel(98), "bien");
  assert.equal(healthLevel(85), "alerta");
  assert.equal(healthLevel(40), "critico");
  assert.equal(healthLevel(null), "sin-datos");
});

test("statusLabel traduce los estados", () => {
  assert.equal(statusLabel("FAILED"), "No cumple");
  assert.equal(statusLabel(undefined), "Sin ejecutar");
});

test("ruleLabel arma el nombre de la regla", () => {
  assert.equal(ruleLabel({ rule_type: "completeness", column: "nit_cliente" }), "Completitud de nit_cliente");
  assert.equal(ruleLabel({ rule_type: "volume", column: null }), "Volumen");
});
