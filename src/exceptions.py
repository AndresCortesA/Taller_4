"""Jerarquía de excepciones personalizadas del sistema Software FJ.

Todas heredan de SoftwareFJError para que las capas superiores puedan
capturar cualquier error de dominio con un único except, sin ocultar
errores de programación (TypeError, AttributeError, etc.).
"""


class SoftwareFJError(Exception):
    """Excepción base del dominio. Incluye un código para facilitar el rastreo en logs."""

    codigo = "FJ-000"

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje

    def __str__(self) -> str:
        return f"[{self.codigo}] {self.mensaje}"


class ConfiguracionError(SoftwareFJError):
    """Variables de entorno ausentes o con formato incorrecto."""

    codigo = "FJ-001"


class ValidacionError(SoftwareFJError):
    """Base para errores de datos de entrada inválidos."""

    codigo = "FJ-100"


class ClienteInvalidoError(ValidacionError):
    """Datos personales del cliente incorrectos."""

    codigo = "FJ-101"


class ServicioInvalidoError(ValidacionError):
    """Parámetros de creación o de uso de un servicio fuera de rango."""

    codigo = "FJ-102"


class ServicioNoDisponibleError(SoftwareFJError):
    """El servicio está deshabilitado o ya reservado en el horario solicitado."""

    codigo = "FJ-200"


class ReservaInvalidaError(SoftwareFJError):
    """La reserva no cumple las reglas de negocio."""

    codigo = "FJ-300"


class EstadoReservaError(ReservaInvalidaError):
    """Transición de estado no permitida (por ejemplo, procesar una reserva cancelada)."""

    codigo = "FJ-301"


class CalculoCostoError(SoftwareFJError):
    """Fallo al calcular el costo de un servicio."""

    codigo = "FJ-400"


class EntidadNoEncontradaError(SoftwareFJError):
    """Se buscó un cliente, servicio o reserva que no existe."""

    codigo = "FJ-500"


class EntidadDuplicadaError(SoftwareFJError):
    """Se intentó registrar una entidad con un identificador ya existente."""

    codigo = "FJ-501"
