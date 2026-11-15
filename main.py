"""Punto de entrada de Software FJ: ejecuta las simulaciones y muestra un resumen."""

import sys

from src.config import obtener_configuracion
from src.exceptions import ConfiguracionError
from src.logger import configurar_logger
from src.services import SistemaReservas
from src.simulaciones import ResultadoSimulacion, construir_simulaciones, ejecutar_simulaciones


def imprimir_resultados(resultados: list[ResultadoSimulacion]) -> None:
    print(f"\n{'N°':<4}{'Simulación':<46}{'Esperado':<28}{'Obtenido':<28}Estado")
    print("-" * 112)
    for r in resultados:
        estado = "OK" if r.cumple else "REVISAR"
        print(f"{r.numero:<4}{r.nombre:<46}{r.esperado:<28}{r.obtenido:<28}{estado}")
        print(f"    {r.detalle}")


def imprimir_resumen(resumen: dict[str, int | float], resultados: list[ResultadoSimulacion]) -> None:
    correctas = sum(r.cumple for r in resultados)
    print("\nResumen del sistema")
    print(f"  Clientes registrados : {resumen['clientes']}")
    print(f"  Servicios registrados: {resumen['servicios']}")
    print(f"  Reservas creadas     : {resumen['reservas']}")
    print(f"  Reservas procesadas  : {resumen['reservas_procesadas']}")
    print(f"  Ingresos totales     : ${resumen['ingresos']:,.2f}")
    print(f"  Simulaciones con el resultado esperado: {correctas}/{len(resultados)}")


def main() -> int:
    try:
        config = obtener_configuracion()
    except ConfiguracionError as error:
        # Sin configuración válida no hay log disponible, por eso se informa por consola.
        print(f"No se pudo iniciar la aplicación: {error}", file=sys.stderr)
        return 1

    logger = configurar_logger(config)
    logger.info("=== Inicio de %s ===", config.nombre_app)

    sistema = SistemaReservas(config, logger)
    resultados = ejecutar_simulaciones(sistema, construir_simulaciones(), logger)

    print(f"{config.nombre_app} - Simulaciones de operación")
    imprimir_resultados(resultados)
    imprimir_resumen(sistema.resumen(), resultados)
    print(f"\nRegistro de eventos y errores: {config.ruta_log}")

    logger.info("=== Fin de %s ===", config.nombre_app)
    return 0 if all(r.cumple for r in resultados) else 2


if __name__ == "__main__":
    sys.exit(main())
