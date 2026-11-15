"""Clase abstracta base para todas las entidades del sistema."""

from abc import ABC, abstractmethod

from src.exceptions import ValidacionError


class Entidad(ABC):
    """Representa cualquier objeto identificable del dominio (cliente, servicio, reserva)."""

    def __init__(self, identificador: str):
        if not isinstance(identificador, str) or not identificador.strip():
            raise ValidacionError("El identificador debe ser un texto no vacío")
        self._id = identificador.strip()

    @property
    def id(self) -> str:
        return self._id

    @abstractmethod
    def describir(self) -> str:
        """Texto legible con la información principal de la entidad."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self._id!r})"
