"""Arma un resumen en Markdown de las pruebas unitarias para la página de la ejecución.

Uso: python scripts/test_summary.py reports/junit.xml coverage.xml
"""

import re
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path


def main(junit_path: str, coverage_path: str) -> None:
    print("## Pruebas unitarias · Plan de Pruebas DHP\n")
    if not Path(junit_path).exists():
        print("No se generó el reporte de pruebas (el job falló antes de ejecutar pytest).")
        return

    root = ET.parse(junit_path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    total = int(suite.get("tests", 0))
    failures = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    passed = total - failures - skipped

    print(f"| Total | Pasaron | Fallaron | Omitidas |\n|---|---|---|---|\n| {total} | {passed} | {failures} | {skipped} |\n")

    if Path(coverage_path).exists():
        rate = float(ET.parse(coverage_path).getroot().get("line-rate", 0)) * 100
        estado = "cumple" if rate >= 80 else "NO cumple"
        print(f"**Cobertura de líneas:** {rate:.1f} % ({estado} el mínimo de 80 %)\n")

    casos: "OrderedDict[str, list[bool]]" = OrderedDict()
    fallidas = []
    for case in suite.iter("testcase"):
        name = case.get("name", "")
        ok = case.find("failure") is None and case.find("error") is None
        match = re.search(r"cp(\d{2})", name)
        if match:
            casos.setdefault(f"CP-{match.group(1)}", []).append(ok)
        if not ok:
            fallidas.append(f"{case.get('classname')}::{name}")

    print("| Caso del plan | Escenarios | Resultado |\n|---|---|---|")
    for cp, resultados in sorted(casos.items()):
        icono = "✅ Pasa" if all(resultados) else "❌ Falla"
        print(f"| {cp} | {len(resultados)} | {icono} |")

    if fallidas:
        print("\n### Pruebas que fallaron\n")
        for f in fallidas:
            print(f"- `{f}`")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
