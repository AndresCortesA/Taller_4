"""Batería de simulaciones que ejercitan casos válidos e inválidos del sistema.

Cada simulación declara qué excepción espera (o None si debe ser exitosa).
El ejecutor captura cualquier error, lo registra en el log y continúa con
la siguiente, de modo que la aplicación nunca se detiene.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.exceptions import (
    CalculoCostoError,
    ClienteInvalidoError,
    EntidadDuplicadaError,
    EntidadNoEncontradaError,
    EstadoReservaError,
    ReservaInvalidaError,
    ServicioInvalidoError,
    ServicioNoDisponibleError,
    SoftwareFJError,
)
from src.models import AlquilerEquipo, AsesoriaEspecializada, Cliente, ReservaSala
from src.services import SistemaReservas


@dataclass(frozen=True)
class Simulacion:
    nombre: str
    accion: Callable[[SistemaReservas], str]
    error_esperado: type[Exception] | None = None


@dataclass(frozen=True)
class ResultadoSimulacion:
    numero: int
    nombre: str
    esperado: str
    obtenido: str
    detalle: str

    @property
    def cumple(self) -> bool:
        return self.esperado == self.obtenido


def _manana(hora: int) -> datetime:
    """Fecha de mañana a la hora indicada; garantiza fechas futuras en cada ejecución."""
    base = datetime.now() + timedelta(days=1)
    return base.replace(hour=hora, minute=0, second=0, microsecond=0)


# Acciones de cada simulación. Retornan un texto con el resultado cuando terminan bien.

def registrar_clientes_validos(sistema: SistemaReservas) -> str:
    sistema.registrar_cliente(Cliente("C001", "Laura Gómez", "1032456789", "laura.gomez@mail.com", "3104567890"))
    sistema.registrar_cliente(Cliente("C002", "Andrés Pérez", "80123456", "andres.perez@mail.com", "3209876543"))
    return f"{len(sistema.clientes)} clientes registrados"


def registrar_cliente_correo_invalido(sistema: SistemaReservas) -> str:
    sistema.registrar_cliente(Cliente("C003", "Marta Ruiz", "52123456", "marta.ruiz-arroba-mail", "3001234567"))
    return "registrado"


def registrar_cliente_documento_duplicado(sistema: SistemaReservas) -> str:
    sistema.registrar_cliente(Cliente("C004", "Laura Duplicada", "1032456789", "otra@mail.com", "3111111111"))
    return "registrado"


def registrar_servicios_validos(sistema: SistemaReservas) -> str:
    sistema.registrar_servicio(ReservaSala("S001", "Sala de juntas", 50_000, capacidad=12))
    sistema.registrar_servicio(AlquilerEquipo("S002", "Portátiles de alto rendimiento", 8_000, cantidad_equipos=5))
    sistema.registrar_servicio(AsesoriaEspecializada("S003", "Asesoría en arquitectura", 120_000, nivel="experto"))
    return "; ".join(s.describir() for s in sistema.servicios)


def crear_servicio_tarifa_negativa(sistema: SistemaReservas) -> str:
    sistema.registrar_servicio(ReservaSala("S004", "Auditorio", -10_000, capacidad=80))
    return "registrado"


def crear_asesoria_nivel_inexistente(sistema: SistemaReservas) -> str:
    sistema.registrar_servicio(AsesoriaEspecializada("S005", "Asesoría legal", 90_000, nivel="maestro"))
    return "registrado"


def reserva_sala_completa(sistema: SistemaReservas) -> str:
    reserva = sistema.crear_reserva("C001", "S001", 3, _manana(9))
    sistema.confirmar_reserva(reserva.id)
    costo = sistema.procesar_reserva(reserva.id)
    return f"{reserva.id} procesada por ${costo:,.2f}"


def reserva_equipos_con_descuento(sistema: SistemaReservas) -> str:
    reserva = sistema.crear_reserva("C002", "S002", 24, _manana(8), descuento=0.15)
    sistema.confirmar_reserva(reserva.id)
    costo = sistema.procesar_reserva(reserva.id)
    return f"{reserva.id} procesada con 15% de descuento por ${costo:,.2f}"


def reserva_horario_ocupado(sistema: SistemaReservas) -> str:
    # La sala S001 ya está ocupada de 9:00 a 12:00 por la simulación anterior.
    sistema.crear_reserva("C002", "S001", 2, _manana(10))
    return "creada"


def reserva_servicio_deshabilitado(sistema: SistemaReservas) -> str:
    sistema.cambiar_disponibilidad("S003", disponible=False)
    try:
        sistema.crear_reserva("C001", "S003", 2, _manana(14))
    finally:
        # Se restablece el servicio aunque la reserva falle, para no afectar otras simulaciones.
        sistema.cambiar_disponibilidad("S003", disponible=True)
    return "creada"


def reserva_horas_no_numericas(sistema: SistemaReservas) -> str:
    sistema.crear_reserva("C001", "S003", "dos", _manana(15))
    return "creada"


def reserva_fecha_pasada(sistema: SistemaReservas) -> str:
    sistema.crear_reserva("C002", "S001", 2, datetime.now() - timedelta(days=3))
    return "creada"


def reserva_cliente_inexistente(sistema: SistemaReservas) -> str:
    sistema.crear_reserva("C999", "S001", 2, _manana(16))
    return "creada"


def procesar_sin_confirmar(sistema: SistemaReservas) -> str:
    reserva = sistema.crear_reserva("C001", "S003", 2, _manana(16))
    sistema.procesar_reserva(reserva.id)
    return "procesada"


def asesoria_valida_y_cancelacion(sistema: SistemaReservas) -> str:
    reserva = sistema.crear_reserva("C002", "S003", 4, _manana(8))
    sistema.confirmar_reserva(reserva.id)
    sistema.cancelar_reserva(reserva.id)
    return f"{reserva.id} confirmada y luego cancelada correctamente"


def procesar_reserva_cancelada(sistema: SistemaReservas) -> str:
    # R0004 es la asesoría cancelada en la simulación anterior.
    sistema.procesar_reserva("R0004")
    return "procesada"


def registrar_cliente_sin_telefono(sistema: SistemaReservas) -> str:
    sistema.registrar_cliente(Cliente("C005", "Pedro Díaz", "79555444", "pedro.diaz@mail.com", None))
    return "registrado"


def calculo_con_descuento_inconsistente(sistema: SistemaReservas) -> str:
    costo = sistema.obtener_servicio("S001").calcular_costo(2, descuento=1.3)
    return f"costo calculado: {costo}"


def construir_simulaciones() -> list[Simulacion]:
    """Lista ordenada de simulaciones; algunas dependen de datos creados por las anteriores."""
    return [
        Simulacion("Registro de clientes válidos", registrar_clientes_validos),
        Simulacion("Cliente con correo inválido", registrar_cliente_correo_invalido, ClienteInvalidoError),
        Simulacion("Cliente con documento duplicado", registrar_cliente_documento_duplicado, EntidadDuplicadaError),
        Simulacion("Creación de tres servicios válidos", registrar_servicios_validos),
        Simulacion("Servicio con tarifa negativa", crear_servicio_tarifa_negativa, ServicioInvalidoError),
        Simulacion("Asesoría con nivel inexistente", crear_asesoria_nivel_inexistente, ServicioInvalidoError),
        Simulacion("Reserva de sala: crear, confirmar y procesar", reserva_sala_completa),
        Simulacion("Alquiler de equipos con descuento", reserva_equipos_con_descuento),
        Simulacion("Reserva en horario ocupado", reserva_horario_ocupado, ServicioNoDisponibleError),
        Simulacion("Reserva de servicio deshabilitado", reserva_servicio_deshabilitado, ServicioNoDisponibleError),
        Simulacion("Reserva con horas no numéricas", reserva_horas_no_numericas, ReservaInvalidaError),
        Simulacion("Reserva con fecha pasada", reserva_fecha_pasada, ReservaInvalidaError),
        Simulacion("Reserva para cliente inexistente", reserva_cliente_inexistente, EntidadNoEncontradaError),
        Simulacion("Procesar reserva sin confirmar", procesar_sin_confirmar, EstadoReservaError),
        Simulacion("Asesoría confirmada y cancelada", asesoria_valida_y_cancelacion),
        Simulacion("Procesar reserva cancelada", procesar_reserva_cancelada, EstadoReservaError),
        Simulacion("Cliente con parámetro faltante", registrar_cliente_sin_telefono, ClienteInvalidoError),
        Simulacion("Cálculo con descuento inconsistente", calculo_con_descuento_inconsistente, CalculoCostoError),
    ]


def ejecutar_simulaciones(
    sistema: SistemaReservas,
    simulaciones: list[Simulacion],
    logger: logging.Logger,
) -> list[ResultadoSimulacion]:
    """Ejecuta cada simulación aislando sus errores para que la aplicación continúe."""
    resultados: list[ResultadoSimulacion] = []

    for numero, simulacion in enumerate(simulaciones, start=1):
        esperado = simulacion.error_esperado.__name__ if simulacion.error_esperado else "Éxito"
        logger.info("Simulación %02d iniciada: %s", numero, simulacion.nombre)
        try:
            detalle = simulacion.accion(sistema)
        except SoftwareFJError as error:
            # Error de negocio controlado: se registra con su causa original, si la hay.
            causa = f" | causa: {type(error.__cause__).__name__}: {error.__cause__}" if error.__cause__ else ""
            logger.error("Simulación %02d: %s%s", numero, error, causa)
            obtenido, detalle = type(error).__name__, f"{error}{causa}"
        except Exception as error:
            # Error no previsto: se guarda la traza completa y el programa sigue.
            logger.exception("Simulación %02d: error inesperado", numero)
            obtenido, detalle = type(error).__name__, f"Error inesperado: {error}"
        else:
            obtenido = "Éxito"
        finally:
            logger.info("Simulación %02d finalizada", numero)

        resultados.append(ResultadoSimulacion(numero, simulacion.nombre, esperado, obtenido, detalle))

    return resultados
