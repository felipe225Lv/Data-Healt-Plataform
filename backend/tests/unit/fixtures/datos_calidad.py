"""Datos de prueba del motor de calidad (Plan de Pruebas, módulo 3)."""

# CP-15: 10 valores, 2 None y 1 cadena vacía -> 70 % de completitud
COLUMNA_CON_FALTANTES = ["900123", "900124", None, "900126", "", "900128", None, "900130", "900131", "900132"]
COLUMNA_COMPLETA = ["A", "B", "C", "D", "E"]

# CP-16: 6 registros con 4 NIT distintos -> 2 duplicados
REGISTROS_CON_DUPLICADOS = [
    {"nit": "9001", "fecha": "2026-11-01"},
    {"nit": "9002", "fecha": "2026-11-01"},
    {"nit": "9001", "fecha": "2026-11-01"},
    {"nit": "9003", "fecha": "2026-11-01"},
    {"nit": "9004", "fecha": "2026-11-01"},
    {"nit": "9002", "fecha": "2026-11-01"},
]
REGISTROS_CLAVE_COMPUESTA = [
    {"nit": "9001", "fecha": "2026-11-01"},
    {"nit": "9001", "fecha": "2026-11-02"},
]

# CP-17: rango [0, 100] con límites incluidos
VALORES_RANGO = [0, 50, 100, -5, 150, None]

# CP-19: 100 valores con 2 nulos (98 %) y con 20 nulos (80 %)
COLUMNA_98 = ["ok"] * 98 + [None] * 2
COLUMNA_80 = ["ok"] * 80 + [None] * 20

# CP-20: historial de volumen con promedio 1000
HISTORIAL_VOLUMEN = [1000, 1020, 980, 1000]
