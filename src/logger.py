"""Configuración centralizada del registro de eventos (logging)."""

import logging

from src.config import Configuracion

FORMATO_LOG = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configurar_logger(config: Configuracion, nombre: str = "software_fj") -> logging.Logger:
    """Devuelve un logger que escribe todos los eventos en el archivo definido en la configuración."""
    logger = logging.getLogger(nombre)

    # Evita duplicar manejadores si la función se llama más de una vez.
    if logger.handlers:
        return logger

    logger.setLevel(config.nivel_log)
    config.ruta_log.parent.mkdir(parents=True, exist_ok=True)

    manejador_archivo = logging.FileHandler(config.ruta_log, encoding="utf-8")
    manejador_archivo.setFormatter(logging.Formatter(FORMATO_LOG))
    logger.addHandler(manejador_archivo)

    # No se propaga al logger raíz: la consola queda reservada para el reporte de resultados.
    logger.propagate = False
    return logger
