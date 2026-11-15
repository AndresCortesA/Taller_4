"""Carga de la configuración desde variables de entorno.

Se lee un archivo .env opcional en la raíz del proyecto. Las variables ya
definidas en el sistema operativo tienen prioridad sobre las del archivo.
No se usan librerías externas para que el proyecto funcione solo con la
biblioteca estándar de Python.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from src.exceptions import ConfiguracionError

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
NIVELES_LOG_VALIDOS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass(frozen=True)
class Configuracion:
    """Valores de configuración inmutables durante la ejecución."""

    nombre_app: str
    ruta_log: Path
    nivel_log: str
    tasa_impuesto: float
    max_horas_reserva: int


def cargar_archivo_env(ruta: Path) -> None:
    """Carga pares CLAVE=valor de un archivo .env en os.environ sin sobrescribir."""
    if not ruta.is_file():
        return

    with ruta.open(encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            # Se ignoran líneas vacías, comentarios y líneas sin '='.
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip("\"'"))


def obtener_configuracion(ruta_env: Path | None = None) -> Configuracion:
    """Construye la configuración validando tipos y rangos de cada variable."""
    cargar_archivo_env(ruta_env or RAIZ_PROYECTO / ".env")

    nivel_log = os.getenv("FJ_NIVEL_LOG", "INFO").upper()
    if nivel_log not in NIVELES_LOG_VALIDOS:
        raise ConfiguracionError(f"FJ_NIVEL_LOG inválido: {nivel_log}")

    ruta_log = Path(os.getenv("FJ_ARCHIVO_LOG", "logs/software_fj.log"))
    if not ruta_log.is_absolute():
        ruta_log = RAIZ_PROYECTO / ruta_log

    try:
        tasa_impuesto = float(os.getenv("FJ_TASA_IMPUESTO", "0.19"))
        max_horas = int(os.getenv("FJ_MAX_HORAS_RESERVA", "72"))
    except ValueError as error:
        # Encadenamiento: se conserva el error original como causa.
        raise ConfiguracionError("FJ_TASA_IMPUESTO o FJ_MAX_HORAS_RESERVA no son numéricos") from error

    if not 0 <= tasa_impuesto < 1:
        raise ConfiguracionError("FJ_TASA_IMPUESTO debe estar entre 0 y 1")
    if max_horas <= 0:
        raise ConfiguracionError("FJ_MAX_HORAS_RESERVA debe ser mayor que cero")

    return Configuracion(
        nombre_app=os.getenv("FJ_NOMBRE_APP", "Software FJ"),
        ruta_log=ruta_log,
        nivel_log=nivel_log,
        tasa_impuesto=tasa_impuesto,
        max_horas_reserva=max_horas,
    )
