"""Pruebas del coordinador, la configuración y la ejecución de simulaciones."""

import logging
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from src.config import Configuracion, obtener_configuracion
from src.exceptions import ConfiguracionError, EntidadDuplicadaError, EntidadNoEncontradaError, ServicioNoDisponibleError
from src.models import Cliente, ReservaSala
from src.services import SistemaReservas
from src.simulaciones import construir_simulaciones, ejecutar_simulaciones


def crear_sistema() -> SistemaReservas:
    config = Configuracion("Pruebas", Path(tempfile.gettempdir()) / "fj_test.log", "INFO", 0.19, 72)
    logger = logging.getLogger("software_fj_pruebas")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return SistemaReservas(config, logger)


class PruebasSistema(unittest.TestCase):
    def setUp(self):
        self.sistema = crear_sistema()
        self.sistema.registrar_cliente(Cliente("C1", "Laura Gómez", "1032456789", "laura@mail.com", "3104567890"))
        self.sistema.registrar_servicio(ReservaSala("S1", "Sala", 10_000, capacidad=5))
        self.inicio = datetime.now() + timedelta(days=1)

    def test_rechaza_id_duplicado(self):
        with self.assertRaises(EntidadDuplicadaError):
            self.sistema.registrar_cliente(Cliente("C1", "Otra Persona", "99999999", "otra@mail.com", "3000000000"))

    def test_rechaza_cruce_de_horarios(self):
        self.sistema.crear_reserva("C1", "S1", 2, self.inicio)
        with self.assertRaises(ServicioNoDisponibleError):
            self.sistema.crear_reserva("C1", "S1", 2, self.inicio + timedelta(hours=1))

    def test_reserva_cancelada_libera_el_horario(self):
        reserva = self.sistema.crear_reserva("C1", "S1", 2, self.inicio)
        self.sistema.cancelar_reserva(reserva.id)
        self.assertEqual(self.sistema.crear_reserva("C1", "S1", 2, self.inicio).id, "R0002")

    def test_busqueda_inexistente(self):
        with self.assertRaises(EntidadNoEncontradaError):
            self.sistema.obtener_reserva("R9999")

    def test_listas_internas_no_se_exponen(self):
        self.assertIsInstance(self.sistema.clientes, tuple)


class PruebasSimulaciones(unittest.TestCase):
    def test_todas_las_simulaciones_dan_el_resultado_esperado(self):
        sistema = crear_sistema()
        resultados = ejecutar_simulaciones(sistema, construir_simulaciones(), logging.getLogger("software_fj_pruebas"))
        self.assertGreaterEqual(len(resultados), 10)
        fallidas = [r.nombre for r in resultados if not r.cumple]
        self.assertEqual(fallidas, [])


class PruebasConfiguracion(unittest.TestCase):
    def test_valor_no_numerico_encadena_value_error(self):
        with mock.patch.dict(os.environ, {"FJ_TASA_IMPUESTO": "diecinueve"}):
            with self.assertRaises(ConfiguracionError) as contexto:
                obtener_configuracion(Path("no_existe.env"))
        self.assertIsInstance(contexto.exception.__cause__, ValueError)

    def test_nivel_de_log_invalido(self):
        with mock.patch.dict(os.environ, {"FJ_NIVEL_LOG": "MUCHO"}):
            with self.assertRaises(ConfiguracionError):
                obtener_configuracion(Path("no_existe.env"))


if __name__ == "__main__":
    unittest.main()
