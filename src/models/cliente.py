"""Modelo de cliente con validación encapsulada en sus propiedades."""

import re

from src.exceptions import ClienteInvalidoError
from src.models.entidad import Entidad

PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]{3,60}$")
PATRON_DOCUMENTO = re.compile(r"^\d{6,12}$")
PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
PATRON_TELEFONO = re.compile(r"^\d{7,10}$")


class Cliente(Entidad):
    """Cliente de Software FJ. Los atributos solo se modifican a través de setters validados."""

    def __init__(self, identificador: str, nombre: str, documento: str, correo: str, telefono: str):
        super().__init__(identificador)
        self.nombre = nombre
        self.documento = documento
        self.correo = correo
        self.telefono = telefono

    @staticmethod
    def _validar(valor: str, patron: re.Pattern, campo: str) -> str:
        """Verifica que el valor sea texto y cumpla el patrón; retorna el valor normalizado."""
        if not isinstance(valor, str) or not patron.fullmatch(valor.strip()):
            raise ClienteInvalidoError(f"{campo} inválido: {valor!r}")
        return valor.strip()

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = self._validar(valor, PATRON_NOMBRE, "Nombre")

    @property
    def documento(self) -> str:
        return self._documento

    @documento.setter
    def documento(self, valor: str) -> None:
        self._documento = self._validar(valor, PATRON_DOCUMENTO, "Documento")

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        self._correo = self._validar(valor, PATRON_CORREO, "Correo").lower()

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        self._telefono = self._validar(valor, PATRON_TELEFONO, "Teléfono")

    def describir(self) -> str:
        return f"Cliente {self.id}: {self.nombre} (doc. {self.documento}, {self.correo})"
