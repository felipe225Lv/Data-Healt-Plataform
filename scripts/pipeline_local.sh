#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Ejecuta en el computador local las mismas etapas del pipeline de GitHub Actions.
# Uso:
#   ./scripts/pipeline_local.sh              → todas las etapas (requiere Docker)
#   ./scripts/pipeline_local.sh --sin-docker → solo lint, pruebas unitarias y build
# En Windows se ejecuta desde Git Bash.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIN_DOCKER=false
[ "${1:-}" = "--sin-docker" ] && SIN_DOCKER=true
ETAPA=""

trap 'echo; echo "✗ PIPELINE DETENIDO en la etapa: $ETAPA"; echo "  Las etapas siguientes no se ejecutaron (no se despliega)."' ERR

etapa() {
  ETAPA="$1"
  echo
  echo "════════════════════════════════════════════════════════════"
  echo "  $1"
  echo "════════════════════════════════════════════════════════════"
}

PY=python3
command -v python3 > /dev/null 2>&1 || PY=python

# ── 1. Checkout ─────────────────────────────────────────────────────────────
etapa "1. Código fuente"
cd "$ROOT"
git rev-parse --short HEAD 2>/dev/null && git status --short | head -20 || echo "(no es un repositorio git)"

# ── 2-4. Backend: dependencias + lint + pruebas unitarias ───────────────────
etapa "2. Backend · instalación de dependencias"
cd "$ROOT/backend"
[ -d .venv ] || $PY -m venv .venv
if [ -f .venv/bin/activate ]; then . .venv/bin/activate; else . .venv/Scripts/activate; fi
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt -r requirements-dev.txt

etapa "3. Backend · análisis de estilo (ruff)"
ruff check app tests

etapa "4. Backend · PRUEBAS UNITARIAS (pytest + cobertura >= 80 %)"
pytest tests/unit --cov=app --cov-report=term-missing --cov-report=html:htmlcov \
  --cov-fail-under=80 --junitxml=reports/junit.xml -v
deactivate

# ── 5. Frontend ─────────────────────────────────────────────────────────────
etapa "5. Frontend · npm ci + lint + build + pruebas"
cd "$ROOT/frontend"
npm ci
npm run lint
npm run build
npm test

if [ "$SIN_DOCKER" = true ]; then
  echo; echo "✓ Pipeline local OK (sin etapas de Docker)"; exit 0
fi

# ── 6-7. Imágenes y despliegue ──────────────────────────────────────────────
etapa "6. Docker · construcción de imágenes"
cd "$ROOT"
docker compose build

etapa "7. Despliegue · docker compose up"
docker compose up -d --wait

etapa "8. Pruebas de humo sobre el ambiente desplegado"
bash scripts/smoke_test.sh http://localhost:8080

echo
echo "✓ PIPELINE LOCAL COMPLETO. Dashboard: http://localhost:8080  ·  API: http://localhost:8000/docs"
