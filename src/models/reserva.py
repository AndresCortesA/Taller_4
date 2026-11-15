"""Modelo de reserva y su ciclo de vida (pendiente, confirmada, cancelada, procesada)."""

from datetime import datetime, timedelta
from enum import Enum

from src.exceptions import EstadoReservaError, ReservaInvalidaError, ServicioNoDisponibleError, ValidacionError
from src.models.cliente import Cliente
from src.models.entidad import Entidad
from src.models.servicio import Servicio

DESCUENTO_MAXIMO = 0.5


class EstadoReserva(Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    PROCESADA = "procesada"


class Reserva(Entidad):
    """Une un cliente con un servicio durante un intervalo de tiempo."""

    def __init__(
        self,
        identificador: str,
        cliente: Cliente,
        servicio: Servicio,
        horas: float,
        fecha_inicio: datetime,
        descuento: float = 0.0,
    ):
        super().__init__(identificador)

        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un cliente válido")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un servicio válido")
        if not servicio.disponible:
            raise ServicioNoDisponibleError(f"El servicio '{servicio.nombre}' no está disponible")

        try:
            servicio.validar_parametros(horas)
        except ValidacionError as error:
            # Se traduce el error del servicio a un error de reserva conservando la causa.
            raise ReservaInvalidaError(f"Duración no válida para la reserva {identificador}") from error

        if not isinstance(fecha_inicio, datetime) or fecha_inicio < datetime.now():
            raise ReservaInvalidaError("La fecha de inicio debe ser una fecha futura, intentar de nuevo")
        if isinstance(descuento, bool) or not isinstance(descuento, (int, float)) or not 0 <= descuento <= DESCUENTO_MAXIMO:
            raise ReservaInvalidaError(f"El descuento debe estar entre 0 y {DESCUENTO_MAXIMO}")

        self._cliente = cliente
        self._servicio = servicio
        self._horas = horas
        self._fecha_inicio = fecha_inicio
        self._descuento = float(descuento)
        self._estado = EstadoReserva.PENDIENTE
        self._costo_total: float | None = None

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def horas(self) -> float:
        return self._horas

    @property
    def fecha_inicio(self) -> datetime:
        return self._fecha_inicio

    @property
    def fecha_fin(self) -> datetime:
        return self._fecha_inicio + timedelta(hours=self._horas)

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    @property
    def costo_total(self) -> float | None:
        return self._costo_total

    @property
    def activa(self) -> bool:
        """Una reserva ocupa el servicio mientras no esté cancelada."""
        return self._estado in (EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA, EstadoReserva.PROCESADA)

    def se_cruza_con(self, inicio: datetime, fin: datetime) -> bool:
        return self.activa and inicio < self.fecha_fin and fin > self.fecha_inicio

    def confirmar(self) -> None:
        if self._estado is not EstadoReserva.PENDIENTE:
            raise EstadoReservaError(f"Solo se confirman reservas pendientes ({self.id} está {self._estado.value})")
        self._estado = EstadoReserva.CONFIRMADA

    def cancelar(self) -> None:
        if self._estado in (EstadoReserva.CANCELADA, EstadoReserva.PROCESADA):
            raise EstadoReservaError(f"La reserva {self.id} ya está {self._estado.value} y no se puede cancelar")
        self._estado = EstadoReserva.CANCELADA

    def procesar(self, tasa_impuesto: float) -> float:
        """Calcula el costo final y marca la reserva como procesada."""
        if self._estado is not EstadoReserva.CONFIRMADA:
            raise EstadoReservaError(f"Solo se procesan reservas confirmadas ({self.id} está {self._estado.value})")
        self._costo_total = self._servicio.calcular_costo(self._horas, self._descuento, tasa_impuesto)
        self._estado = EstadoReserva.PROCESADA
        return self._costo_total

    def describir(self) -> str:
        costo = f" - total ${self._costo_total:,.2f}" if self._costo_total is not None else ""
        return (
            f"Reserva {self.id}: {self.cliente.nombre} -> {self.servicio.nombre}, "
            f"{self.horas} h desde {self.fecha_inicio:%Y-%m-%d %H:%M} [{self.estado.value}]{costo}"
        )
