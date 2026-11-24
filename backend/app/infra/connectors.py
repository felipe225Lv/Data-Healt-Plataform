"""Conectores a las fuentes de datos.

En esta versión del aplicativo está implementado el conector de archivos CSV.
Los motores relacionales (PostgreSQL / MySQL) quedan declarados para la
siguiente iteración y responden con error de conexión.
"""

import csv
from pathlib import Path


class CsvConnector:
    """Lee archivos CSV de una carpeta. El nombre del conjunto es el nombre del archivo."""

    def __init__(self, folder: str):
        self.folder = Path(folder)

    def ping(self) -> bool:
        if not self.folder.is_dir():
            raise ConnectionError(f"No existe la carpeta {self.folder}")
        return True

    def fetch_column(self, dataset_name: str, column: str) -> list:
        path = self.folder / dataset_name
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if column not in (reader.fieldnames or []):
                raise KeyError(f"La columna '{column}' no existe en {dataset_name}")
            return [row[column] if row[column] != "" else None for row in reader]

    def close(self) -> None:
        pass


class UnsupportedConnector:
    def __init__(self, engine: str):
        self.engine = engine

    def ping(self):
        raise ConnectionError(f"Conector {self.engine} no disponible en esta versión")

    def fetch_column(self, dataset_name, column):
        raise ConnectionError(f"Conector {self.engine} no disponible en esta versión")

    def close(self) -> None:
        pass


class ConnectorFactory:
    def create(self, source, password=None):
        if source.type == "csv":
            return CsvConnector(source.database or ".")
        return UnsupportedConnector(source.type)
