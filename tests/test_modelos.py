"""Pruebas de los modelos: validaciones, polimorfismo y encadenamiento de excepciones."""

import unittest
from datetime import datetime, timedelta

from src.exceptions import (
    CalculoCostoError,
    ClienteInvalidoError,
    EstadoReservaError,
    ReservaInvalidaError,
    ServicioInvalidoError,
    ServicioNoDisponibleError,
)
from src.models import AlquilerEquipo, AsesoriaEspecializada, Cliente, EstadoReserva, Reserva, ReservaSala


def cliente_valido() -> Cliente:
    return Cliente("C001", "Laura Gómez", "1032456789", "Laura@Mail.com", "3104567890")


def manana() -> datetime:
    return datetime.now() + timedelta(days=1)


class PruebasCliente(unittest.TestCase):
    def test_normaliza_correo(self):
        self.assertEqual(cliente_valido().correo, "laura@mail.com")

    def test_rechaza_documento_con_letras(self):
        with self.assertRaises(ClienteInvalidoError):
            Cliente("C002", "Ana Ruiz", "12AB56", "ana@mail.com", "3001234567")

    def test_setter_valida_despues_de_creado(self):
        cliente = cliente_valido()
        with self.assertRaises(ClienteInvalidoError):
            cliente.telefono = "123"


class PruebasServicios(unittest.TestCase):
    def test_costo_polimorfico_por_tipo(self):
        sala = ReservaSala("S1", "Sala", 10_000, capacidad=5)
        equipo = AlquilerEquipo("S2", "Portátiles", 1_000, cantidad_equipos=2)
        asesoria = AsesoriaEspecializada("S3", "Asesoría", 10_000, nivel="avanzado")
        self.assertEqual(sala.calcular_costo(2), 20_000)
        self.assertEqual(equipo.calcular_costo(2), 2 * (2_000 + 15_000))
        self.assertEqual(asesoria.calcular_costo(2), 30_000)

    def test_variantes_de_calcular_costo(self):
        sala = ReservaSala("S1", "Sala", 10_000, capacidad=5)
        self.assertEqual(sala.calcular_costo(2, descuento=0.1), 18_000)
        self.assertEqual(sala.calcular_costo(2, tasa_impuesto=0.19), 23_800)

    def test_recargo_por_jornada_extendida(self):
        sala = ReservaSala("S1", "Sala", 10_000, capacidad=5)
        self.assertEqual(sala.calcular_costo(10), 110_000)

    def test_validaciones_propias_de_cada_subclase(self):
        with self.assertRaises(ServicioInvalidoError):
            ReservaSala("S1", "Sala", 10_000, capacidad=5).validar_parametros(1.25)
        with self.assertRaises(ServicioInvalidoError):
            AlquilerEquipo("S2", "Equipos", 1_000, cantidad_equipos=1).validar_parametros(1)
        with self.assertRaises(ServicioInvalidoError):
            AsesoriaEspecializada("S3", "Asesoría", 1_000, nivel="basico").validar_parametros(1.5)

    def test_encadena_error_de_calculo(self):
        class ServicioDefectuoso(ReservaSala):
            def costo_base(self, horas):
                return horas / 0

        with self.assertRaises(CalculoCostoError) as contexto:
            ServicioDefectuoso("S9", "Defectuoso", 1_000, capacidad=1).calcular_costo(2)
        self.assertIsInstance(contexto.exception.__cause__, ZeroDivisionError)


class PruebasReserva(unittest.TestCase):
    def setUp(self):
        self.sala = ReservaSala("S1", "Sala", 10_000, capacidad=5)
        self.reserva = Reserva("R1", cliente_valido(), self.sala, 2, manana())

    def test_flujo_completo(self):
        self.reserva.confirmar()
        self.assertEqual(self.reserva.procesar(0.19), 23_800)
        self.assertIs(self.reserva.estado, EstadoReserva.PROCESADA)

    def test_no_procesa_sin_confirmar(self):
        with self.assertRaises(EstadoReservaError):
            self.reserva.procesar(0.19)

    def test_no_cancela_dos_veces(self):
        self.reserva.cancelar()
        with self.assertRaises(EstadoReservaError):
            self.reserva.cancelar()

    def test_horas_invalidas_conservan_la_causa(self):
        with self.assertRaises(ReservaInvalidaError) as contexto:
            Reserva("R2", cliente_valido(), self.sala, 50, manana())
        self.assertIsInstance(contexto.exception.__cause__, ServicioInvalidoError)

    def test_servicio_deshabilitado(self):
        self.sala.deshabilitar()
        with self.assertRaises(ServicioNoDisponibleError):
            Reserva("R3", cliente_valido(), self.sala, 2, manana())


if __name__ == "__main__":
    unittest.main()
