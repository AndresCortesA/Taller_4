"""Coordinador del sistema: administra clientes, servicios y reservas en listas internas.

No se usa base de datos; la información vive en memoria durante la ejecución
y solo los eventos y errores se escriben en el archivo de logs.
"""

import logging
from datetime import datetime
from typing import TypeVar

from src.config import Configuracion
from src.exceptions import (
    CalculoCostoError,
    EntidadDuplicadaError,
    EntidadNoEncontradaError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
)
from src.models import Cliente, Entidad, Reserva, Servicio

T = TypeVar("T", bound=Entidad)


class SistemaReservas:
    """Punto único de acceso a las operaciones de negocio de Software FJ."""

    def __init__(self, config: Configuracion, logger: logging.Logger):
        self._config = config
        self._logger = logger
        self._clientes: list[Cliente] = []
        self._servicios: list[Servicio] = []
        self._reservas: list[Reserva] = []
        self._consecutivo_reserva = 0

    # Consultas

    @property
    def clientes(self) -> tuple[Cliente, ...]:
        # Se expone una tupla para que el exterior no modifique la lista interna.
        return tuple(self._clientes)

    @property
    def servicios(self) -> tuple[Servicio, ...]:
        return tuple(self._servicios)

    @property
    def reservas(self) -> tuple[Reserva, ...]:
        return tuple(self._reservas)

    @staticmethod
    def _buscar(coleccion: list[T], identificador: str, tipo: str) -> T:
        """Busca por id dentro de una lista; lanza EntidadNoEncontradaError si no existe."""
        for entidad in coleccion:
            if entidad.id == identificador:
                return entidad
        raise EntidadNoEncontradaError(f"{tipo} '{identificador}' no existe")

    def obtener_cliente(self, cliente_id: str) -> Cliente:
        return self._buscar(self._clientes, cliente_id, "Cliente")

    def obtener_servicio(self, servicio_id: str) -> Servicio:
        return self._buscar(self._servicios, servicio_id, "Servicio")

    def obtener_reserva(self, reserva_id: str) -> Reserva:
        return self._buscar(self._reservas, reserva_id, "Reserva")

    # Registro de clientes y servicios

    def registrar_cliente(self, cliente: Cliente) -> Cliente:
        """Agrega un cliente verificando que su id y documento no estén repetidos."""
        try:
            self.obtener_cliente(cliente.id)
        except EntidadNoEncontradaError:
            # El id está libre; se verifica también el documento.
            if any(c.documento == cliente.documento for c in self._clientes):
                raise EntidadDuplicadaError(f"Ya existe un cliente con documento {cliente.documento}") from None
            self._clientes.append(cliente)
        else:
            # El bloque else solo se ejecuta si la búsqueda encontró al cliente.
            raise EntidadDuplicadaError(f"Ya existe un cliente con id {cliente.id}")

        self._logger.info("Cliente registrado: %s", cliente.describir())
        return cliente

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        if any(s.id == servicio.id for s in self._servicios):
            raise EntidadDuplicadaError(f"Ya existe un servicio con id {servicio.id}")
        self._servicios.append(servicio)
        self._logger.info("Servicio registrado: %s", servicio.describir())
        return servicio

    def cambiar_disponibilidad(self, servicio_id: str, disponible: bool) -> None:
        servicio = self.obtener_servicio(servicio_id)
        if disponible:
            servicio.habilitar()
        else:
            servicio.deshabilitar()
        self._logger.info("Servicio %s marcado como %s", servicio_id, "disponible" if disponible else "no disponible")

    # Ciclo de vida de reservas

    def crear_reserva(
        self,
        cliente_id: str,
        servicio_id: str,
        horas: float,
        fecha_inicio: datetime,
        descuento: float = 0.0,
    ) -> Reserva:
        """Crea una reserva pendiente tras validar cliente, servicio, duración y horario."""
        cliente = self.obtener_cliente(cliente_id)
        servicio = self.obtener_servicio(servicio_id)

        reserva = Reserva(self._siguiente_id_reserva(), cliente, servicio, horas, fecha_inicio, descuento)

        if reserva.horas > self._config.max_horas_reserva:
            raise ReservaInvalidaError(
                f"La reserva supera el máximo permitido de {self._config.max_horas_reserva} horas"
            )

        # Un servicio no puede tener dos reservas activas que se crucen en el tiempo.
        for existente in self._reservas:
            if existente.servicio is servicio and existente.se_cruza_con(reserva.fecha_inicio, reserva.fecha_fin):
                raise ServicioNoDisponibleError(
                    f"'{servicio.nombre}' ya está reservado entre "
                    f"{existente.fecha_inicio:%Y-%m-%d %H:%M} y {existente.fecha_fin:%H:%M}"
                )

        self._reservas.append(reserva)
        self._consecutivo_reserva += 1
        self._logger.info("Reserva creada: %s", reserva.describir())
        return reserva

    def _siguiente_id_reserva(self) -> str:
        # El consecutivo solo avanza cuando la reserva se guarda, así no quedan huecos.
        return f"R{self._consecutivo_reserva + 1:04d}"

    def confirmar_reserva(self, reserva_id: str) -> Reserva:
        reserva = self.obtener_reserva(reserva_id)
        reserva.confirmar()
        self._logger.info("Reserva confirmada: %s", reserva_id)
        return reserva

    def cancelar_reserva(self, reserva_id: str) -> Reserva:
        reserva = self.obtener_reserva(reserva_id)
        reserva.cancelar()
        self._logger.info("Reserva cancelada: %s", reserva_id)
        return reserva

    def procesar_reserva(self, reserva_id: str) -> float:
        """Calcula el cobro de una reserva confirmada.

        Usa try/except/else/finally: el else registra el éxito y el finally
        deja constancia de que el intento terminó, haya fallado o no.
        """
        reserva = self.obtener_reserva(reserva_id)
        self._logger.debug("Inicio de procesamiento de %s", reserva_id)
        try:
            costo = reserva.procesar(self._config.tasa_impuesto)
        except CalculoCostoError:
            self._logger.error("Cálculo inconsistente en %s; la reserva queda confirmada", reserva_id)
            raise
        else:
            self._logger.info("Reserva procesada: %s", reserva.describir())
            return costo
        finally:
            self._logger.debug("Fin de procesamiento de %s", reserva_id)

    # Reportes

    def resumen(self) -> dict[str, int | float]:
        """Totales generales para mostrar al final de la ejecución."""
        procesadas = [r for r in self._reservas if r.costo_total is not None]
        return {
            "clientes": len(self._clientes),
            "servicios": len(self._servicios),
            "reservas": len(self._reservas),
            "reservas_procesadas": len(procesadas),
            "ingresos": round(sum(r.costo_total for r in procesadas), 2),
        }

