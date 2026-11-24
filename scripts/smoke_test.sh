#!/usr/bin/env bash
# Pruebas de humo sobre el ambiente desplegado.
# Uso: scripts/smoke_test.sh [URL_BASE]   (por defecto http://localhost:8080)
set -euo pipefail

BASE="${1:-http://localhost:8080}"
API="$BASE/api/v1"

echo "→ Verificando salud de la API en $API/health"
for i in $(seq 1 20); do
  if curl -fsS "$API/health" > /dev/null; then break; fi
  if [ "$i" -eq 20 ]; then echo "✗ La API no respondió"; exit 1; fi
  sleep 3
done
echo "✓ /health responde"

echo "→ Iniciando sesión con el usuario analista"
LOGIN=$(curl -fsS -X POST "$API/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"analista@dhp.test","password":"Analista#2026"}')
TOKEN=$(echo "$LOGIN" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
[ -n "$TOKEN" ] || { echo "✗ No se obtuvo token"; exit 1; }
echo "✓ Login correcto (token JWT recibido)"

echo "→ Consultando el resumen del dashboard"
SUMMARY=$(curl -fsS "$API/dashboard/summary" -H "Authorization: Bearer $TOKEN")
echo "$SUMMARY" | grep -q '"sources"' || { echo "✗ Respuesta inesperada: $SUMMARY"; exit 1; }
echo "✓ Dashboard: $SUMMARY"

echo "→ Verificando que el dashboard web carga"
curl -fsS "$BASE/" | grep -q "Data Health Platform" || { echo "✗ El dashboard no cargó"; exit 1; }
echo "✓ Dashboard web disponible en $BASE"

echo "→ Verificando control de acceso (NEGOCIO no puede crear fuentes)"
TOKEN_NEG=$(curl -fsS -X POST "$API/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"negocio@dhp.test","password":"Negocio#2026"}' | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API/sources" -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_NEG" -d '{"name":"Prueba","type":"csv","database":"/tmp"}')
[ "$CODE" = "403" ] || { echo "✗ Se esperaba 403 y llegó $CODE"; exit 1; }
echo "✓ Acceso denegado correctamente (403)"

echo "Pruebas de humo OK"
