"""Servicios ofrecidos por Software FJ.

Servicio es abstracta: define el flujo común de cálculo de costos y cada
subclase aporta su propia regla de costo y de validación (polimorfismo).
"""

from abc import abstractmethod

from src.exceptions import CalculoCostoError, ServicioInvalidoError
from src.models.entidad import Entidad


class Servicio(Entidad):
    """Servicio genérico con tarifa por hora y estado de disponibilidad."""

    HORAS_MINIMAS = 1
    HORAS_MAXIMAS = 12

    def __init__(self, identificador: str, nombre: str, tarifa_hora: float):
        super().__init__(identificador)
        if not isinstance(nombre, str) or len(nombre.strip()) < 3:
            raise ServicioInvalidoError("El nombre del servicio debe tener al menos 3 caracteres")
        # bool es subclase de int, por eso se excluye de forma explícita.
        if isinstance(tarifa_hora, bool) or not isinstance(tarifa_hora, (int, float)) or tarifa_hora <= 0:
            raise ServicioInvalidoError(f"Tarifa inválida para '{nombre}': {tarifa_hora!r}")
        self._nombre = nombre.strip()
        self._tarifa_hora = float(tarifa_hora)
        self._disponible = True

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_hora(self) -> float:
        return self._tarifa_hora

    @property
    def disponible(self) -> bool:
        return self._disponible

    def habilitar(self) -> None:
        self._disponible = True

    def deshabilitar(self) -> None:
        self._disponible = False

    def validar_parametros(self, horas: float) -> None:
        """Valida la duración solicitada según los límites de cada tipo de servicio."""
        if isinstance(horas, bool) or not isinstance(horas, (int, float)):
            raise ServicioInvalidoError(f"Las horas deben ser numéricas, se recibió {horas!r}")
        if not self.HORAS_MINIMAS <= horas <= self.HORAS_MAXIMAS:
            raise ServicioInvalidoError(
                f"{self.nombre}: la duración debe estar entre "
                f"{self.HORAS_MINIMAS} y {self.HORAS_MAXIMAS} horas (se pidió {horas})"
            )

    @abstractmethod
    def costo_base(self, horas: float) -> float:
        """Costo antes de descuentos e impuestos. Cada subclase lo sobrescribe con su regla."""

    def calcular_costo(self, horas: float, descuento: float = 0.0, tasa_impuesto: float = 0.0) -> float:
        """Calcula el costo total.

        Los parámetros opcionales permiten usar el método de varias formas
        (solo horas, con descuento, con impuesto), a modo de sobrecarga.
        """
        if not 0 <= descuento < 1:
            raise CalculoCostoError(f"Descuento fuera de rango: {descuento}")
        self.validar_parametros(horas)

        try:
            subtotal = self.costo_base(horas)
        except (TypeError, ValueError, ArithmeticError) as error:
            raise CalculoCostoError(f"No fue posible calcular el costo de '{self.nombre}'") from error

        return round(subtotal * (1 - descuento) * (1 + tasa_impuesto), 2)

    def describir(self) -> str:
        estado = "disponible" if self.disponible else "no disponible"
        return f"{type(self).__name__} {self.id}: {self.nombre} - ${self.tarifa_hora:,.0f}/h ({estado})"


class ReservaSala(Servicio):
    """Alquiler de salas por horas. Se aplica recargo si se supera la jornada de 8 horas."""

    HORAS_MAXIMAS = 12
    RECARGO_JORNADA_EXTENDIDA = 0.10

    def __init__(self, identificador: str, nombre: str, tarifa_hora: float, capacidad: int):
        super().__init__(identificador, nombre, tarifa_hora)
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) or capacidad <= 0:
            raise ServicioInvalidoError(f"Capacidad inválida para la sala: {capacidad!r}")
        self._capacidad = capacidad

    @property
    def capacidad(self) -> int:
        return self._capacidad

    def validar_parametros(self, horas: float) -> None:
        """Además del rango general, las salas se reservan en bloques de media hora."""
        super().validar_parametros(horas)
        if (horas * 2) % 1 != 0:
            raise ServicioInvalidoError(f"{self.nombre}: las salas se reservan en bloques de 30 minutos")

    def costo_base(self, horas: float) -> float:
        costo = self.tarifa_hora * horas
        if horas > 8:
            costo *= 1 + self.RECARGO_JORNADA_EXTENDIDA
        return costo

    def describir(self) -> str:
        return f"{super().describir()} - capacidad {self.capacidad} personas"


class AlquilerEquipo(Servicio):
    """Alquiler de equipos tecnológicos. Incluye un seguro fijo por cada equipo."""

    HORAS_MAXIMAS = 72
    HORAS_MINIMAS_ALQUILER = 2
    SEGURO_POR_EQUIPO = 15_000

    def __init__(self, identificador: str, nombre: str, tarifa_hora: float, cantidad_equipos: int):
        super().__init__(identificador, nombre, tarifa_hora)
        if isinstance(cantidad_equipos, bool) or not isinstance(cantidad_equipos, int) or cantidad_equipos <= 0:
            raise ServicioInvalidoError(f"Cantidad de equipos inválida: {cantidad_equipos!r}")
        self._cantidad_equipos = cantidad_equipos

    @property
    def cantidad_equipos(self) -> int:
        return self._cantidad_equipos

    def validar_parametros(self, horas: float) -> None:
        """Los equipos se alquilan por un mínimo de 2 horas."""
        super().validar_parametros(horas)
        if horas < self.HORAS_MINIMAS_ALQUILER:
            raise ServicioInvalidoError(f"{self.nombre}: el alquiler mínimo es de {self.HORAS_MINIMAS_ALQUILER} horas")

    def costo_base(self, horas: float) -> float:
        return self.cantidad_equipos * (self.tarifa_hora * horas + self.SEGURO_POR_EQUIPO)

    def describir(self) -> str:
        return f"{super().describir()} - {self.cantidad_equipos} equipo(s)"


class AsesoriaEspecializada(Servicio):
    """Asesoría profesional cuyo valor depende del nivel del asesor."""

    HORAS_MAXIMAS = 8
    MULTIPLICADORES = {"basico": 1.0, "avanzado": 1.5, "experto": 2.0}

    def __init__(self, identificador: str, nombre: str, tarifa_hora: float, nivel: str):
        super().__init__(identificador, nombre, tarifa_hora)
        nivel_normalizado = nivel.strip().lower() if isinstance(nivel, str) else nivel
        if nivel_normalizado not in self.MULTIPLICADORES:
            raise ServicioInvalidoError(
                f"Nivel '{nivel}' no existe. Opciones: {', '.join(self.MULTIPLICADORES)}"
            )
        self._nivel = nivel_normalizado

    @property
    def nivel(self) -> str:
        return self._nivel

    def validar_parametros(self, horas: float) -> None:
        """Las asesorías se agendan solo por horas completas."""
        super().validar_parametros(horas)
        if horas != int(horas):
            raise ServicioInvalidoError(f"{self.nombre}: las asesorías se agendan por horas completas")

    def costo_base(self, horas: float) -> float:
        return self.tarifa_hora * horas * self.MULTIPLICADORES[self.nivel]

    def describir(self) -> str:
        return f"{super().describir()} - nivel {self.nivel}"
