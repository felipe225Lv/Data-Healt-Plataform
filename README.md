# Data Health Platform (DHP)

Plataforma web de observabilidad y alertas de calidad de datos para pymes.
Proyecto de Ingeniería de Software III, Institución Universitaria EAM.

**Integrantes:** Cristian Felipe Lopez · Esteban Pineda Ardila

Este repositorio contiene el aplicativo, las **pruebas unitarias definidas en el Plan de Pruebas (CP-01 a CP-25)** y el **pipeline CI/CD** en GitHub Actions que las ejecuta automáticamente antes de desplegar.

## Stack

| Parte | Tecnología |
|---|---|
| API | Python 3.12, FastAPI, Pydantic, PyJWT, cryptography (Fernet) |
| Pruebas unitarias | pytest, pytest-cov, unittest.mock (MagicMock), freezegun |
| Calidad de código | ruff |
| Dashboard | HTML + JavaScript (sin dependencias), servido con Nginx |
| Contenedores | Docker y Docker Compose |
| Pipeline | GitHub Actions (`.github/workflows/ci-cd.yml`) |

## Estructura

```
data-health-platform/
├── .github/workflows/ci-cd.yml   ← pipeline
├── backend/
│   ├── app/
│   │   ├── services/             ← lógica de negocio (Auth, User, DataSource, Dataset, Rule, Incident, Alert, Report)
│   │   ├── engine/               ← motor de calidad (métricas, detector de anomalías, ValidationRunner)
│   │   ├── core/                 ← permisos, seguridad, excepciones, reloj
│   │   ├── domain/               ← entidades y DTO
│   │   ├── api/                  ← endpoints REST
│   │   ├── repositories/ infra/  ← repositorios en memoria, conectores, notificador, scheduler
│   │   └── main.py
│   ├── tests/unit/               ← PRUEBAS UNITARIAS (una por cada caso del plan)
│   ├── sample_data/ventas.csv    ← datos de demostración (20 % de NIT vacíos)
│   ├── requirements.txt · requirements-dev.txt · pyproject.toml · Dockerfile
├── frontend/                     ← dashboard (npm ci, lint, build, test) + Dockerfile + nginx.conf
├── scripts/
│   ├── pipeline_local.sh         ← las mismas etapas del pipeline, en el computador local
│   ├── smoke_test.sh             ← pruebas de humo después del despliegue
│   └── test_summary.py           ← resumen de resultados por caso del plan
└── docker-compose.yml
```

## Ejecutar el pipeline

### Opción A: GitHub Actions

1. Hacer **fork** de este repositorio (o subirlo a un repositorio propio).
2. En el fork, entrar a la pestaña **Actions** y pulsar *I understand my workflows, go ahead and enable them*.
3. Hacer un cambio y un `push` a `main` o `develop`, o ejecutar el workflow **DHP CI/CD** con *Run workflow*.
4. No hay que configurar secretos: el despliegue se hace en el propio runner con Docker Compose y se valida con pruebas de humo.

### Opción B: local

Requisitos: Git, Python 3.12, Node.js 20 y Docker Desktop (en Windows, usar **Git Bash**).

```bash
./scripts/pipeline_local.sh              # todas las etapas
./scripts/pipeline_local.sh --sin-docker # solo lint, pruebas unitarias y build
```

Dashboard: http://localhost:8080 · Documentación de la API: http://localhost:8000/docs

### Solo las pruebas unitarias

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/unit --cov=app --cov-report=term-missing --cov-fail-under=80 -v
```

## Provocar un fallo

Cambie el valor esperado de cualquier prueba, por ejemplo en `backend/tests/unit/test_metrics.py`:

```python
assert calculate_completeness(COLUMNA_CON_FALTANTES) == pytest.approx(70.0)   # cambiar 70.0 por 75.0
```

Al hacer push, el job **Backend · Pruebas unitarias** termina en rojo, el resumen de la ejecución muestra qué caso del plan falló y los jobs **Docker** y **Deploy** quedan omitidos: no se despliega nada.

## Trazabilidad con el Plan de Pruebas

| Caso | Método | Archivo de prueba |
|---|---|---|
| CP-01 | AuthService.authenticate() | test_auth_service.py |
| CP-02 a CP-05 | UserService.create_user / update_user / deactivate_user / list_users | test_user_service.py |
| CP-06 | PermissionChecker.has_permission() | test_permissions.py |
| CP-07 a CP-10 | DataSourceService.create_source / test_connection / update_source / delete_source | test_datasource_service.py |
| CP-11, CP-12 | DatasetService.register_dataset / list_by_source | test_dataset_service.py |
| CP-13, CP-14 | RuleService.create_rule / update_rule | test_rule_service.py |
| CP-15 a CP-18 | calculate_completeness / uniqueness / validity / freshness | test_metrics.py |
| CP-19 | ValidationRunner.run_validation() | test_validation_runner.py |
| CP-20, CP-21 | AnomalyDetector.detect_volume_anomaly / detect_schema_change | test_anomaly_detector.py |
| CP-22, CP-23 | IncidentService.create_incident / close_incident | test_incident_service.py |
| CP-24 | AlertService.send_alert() | test_alert_service.py |
| CP-25 | ReportService.generate_quality_report() | test_report_service.py |

Cada función de prueba empieza por `test_cpXX_` para identificar el caso del plan.

## Usuarios de demostración

| Correo | Contraseña | Rol |
|---|---|---|
| admin@dhp.test | Admin#2026 | ADMIN |
| analista@dhp.test | Analista#2026 | ANALISTA |
| negocio@dhp.test | Negocio#2026 | NEGOCIO |

Los datos se guardan en memoria y se reinician con el contenedor.

prueba 1
prueba 2