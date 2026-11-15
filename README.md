# Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas

Proyecto de la Fase 4 (Componente práctico - Prácticas simuladas) del curso Programación (213023) de la UNAD.

Es una aplicación orientada a objetos que gestiona clientes, servicios (salas, alquiler de equipos y asesorías especializadas) y reservas sin usar base de datos. La información se mantiene en listas internas y solo los eventos y errores se guardan en un archivo de logs. El sistema sigue funcionando aunque se presenten errores durante la ejecución.

## Requisitos

- Python 3.10 o superior.
- No necesita librerías externas; solo usa la biblioteca estándar.

## Ejecución

```bash
# 1. (Opcional) crear el archivo de configuración a partir de la plantilla
cp .env.example .env          # En Windows: copy .env.example .env

# 2. Ejecutar las simulaciones
python main.py

# 3. Ejecutar las pruebas unitarias
python -m unittest -v
```

La consola muestra una tabla con cada simulación, el resultado esperado y el obtenido. El detalle completo queda en `logs/software_fj.log`.

## Variables de entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `FJ_NOMBRE_APP` | `Software FJ` | Nombre que aparece en reportes y logs |
| `FJ_ARCHIVO_LOG` | `logs/software_fj.log` | Ruta del archivo de logs |
| `FJ_NIVEL_LOG` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` o `CRITICAL` |
| `FJ_TASA_IMPUESTO` | `0.19` | Impuesto aplicado al procesar una reserva |
| `FJ_MAX_HORAS_RESERVA` | `72` | Duración máxima de una reserva en horas |

Las variables definidas en el sistema operativo tienen prioridad sobre las del archivo `.env`. Si un valor no es válido, la aplicación informa el error y termina con código 1 antes de procesar datos.

## Estructura

```
software_fj/
├── main.py                       Punto de entrada
├── .env.example                  Plantilla de variables de entorno
├── src/
│   ├── config.py                 Carga y validación de la configuración
│   ├── logger.py                 Configuración del archivo de logs
│   ├── exceptions.py             Jerarquía de excepciones personalizadas
│   ├── simulaciones.py           Batería de 18 simulaciones y su ejecutor
│   ├── models/
│   │   ├── entidad.py            Clase abstracta base (Entidad)
│   │   ├── cliente.py            Cliente con validaciones y encapsulación
│   │   ├── servicio.py           Servicio abstracto y sus tres especializaciones
│   │   └── reserva.py            Reserva y su ciclo de estados
│   └── services/
│       └── sistema_reservas.py   Coordinador con las listas internas
├── tests/                        Pruebas unitarias (unittest)
├── logs/                         Carpeta del archivo de logs
└── docs/GUIA_GITHUB.md           Pasos para publicar el proyecto en GitHub
```

## Cumplimiento del enunciado (Anexo 3)

| Requisito | Dónde se implementa |
|---|---|
| Clase abstracta de entidades generales | `Entidad` en `src/models/entidad.py` |
| Cliente con validaciones y encapsulación | `Cliente`: atributos privados con propiedades que validan con expresiones regulares |
| Servicio abstracto y tres servicios especializados | `Servicio`, `ReservaSala`, `AlquilerEquipo`, `AsesoriaEspecializada` |
| Métodos sobrescritos (costo, descripción, validación) | `costo_base`, `describir` y `validar_parametros` en cada subclase |
| Métodos sobrecargados | `calcular_costo(horas, descuento=0.0, tasa_impuesto=0.0)` admite varias formas de llamado |
| Reserva con confirmación, cancelación y procesamiento | `Reserva.confirmar`, `cancelar`, `procesar` con estados en `EstadoReserva` |
| Listas internas, sin base de datos | `SistemaReservas._clientes`, `_servicios`, `_reservas` |
| Excepciones personalizadas | `src/exceptions.py` (10 clases que heredan de `SoftwareFJError`) |
| `try/except` | `ejecutar_simulaciones`, `main` |
| `try/except/else` | `SistemaReservas.registrar_cliente` |
| `try/except/else/finally` | `SistemaReservas.procesar_reserva`, `ejecutar_simulaciones` |
| `try/finally` | Simulación `reserva_servicio_deshabilitado` (restablece el servicio) |
| Encadenamiento (`raise ... from`) | `Reserva.__init__`, `Servicio.calcular_costo`, `config.obtener_configuracion` |
| Archivo de logs | `src/logger.py`; cada evento y error queda en `logs/software_fj.log` |
| Al menos 10 operaciones simuladas | 18 simulaciones en `src/simulaciones.py` (6 válidas y 12 inválidas) |

## Simulaciones incluidas

| N° | Caso | Resultado esperado |
|---|---|---|
| 1 | Registro de clientes válidos | Éxito |
| 2 | Cliente con correo inválido | `ClienteInvalidoError` |
| 3 | Cliente con documento duplicado | `EntidadDuplicadaError` |
| 4 | Creación de tres servicios válidos | Éxito |
| 5 | Servicio con tarifa negativa | `ServicioInvalidoError` |
| 6 | Asesoría con nivel inexistente | `ServicioInvalidoError` |
| 7 | Reserva de sala: crear, confirmar y procesar | Éxito |
| 8 | Alquiler de equipos con descuento | Éxito |
| 9 | Reserva en horario ocupado | `ServicioNoDisponibleError` |
| 10 | Reserva de servicio deshabilitado | `ServicioNoDisponibleError` |
| 11 | Reserva con horas no numéricas | `ReservaInvalidaError` (causa: `ServicioInvalidoError`) |
| 12 | Reserva con fecha pasada | `ReservaInvalidaError` |
| 13 | Reserva para cliente inexistente | `EntidadNoEncontradaError` |
| 14 | Procesar reserva sin confirmar | `EstadoReservaError` |
| 15 | Asesoría confirmada y cancelada | Éxito |
| 16 | Procesar reserva cancelada | `EstadoReservaError` |
| 17 | Cliente con parámetro faltante | `ClienteInvalidoError` |
| 18 | Cálculo con descuento inconsistente | `CalculoCostoError` |

## Reglas de negocio de los servicios

| Servicio | Duración permitida | Cálculo del costo base |
|---|---|---|
| Reserva de sala | 1 a 12 h, en bloques de 30 min | tarifa x horas; +10 % si supera 8 h |
| Alquiler de equipos | 2 a 72 h | equipos x (tarifa x horas + seguro de $15.000) |
| Asesoría especializada | 1 a 8 h completas | tarifa x horas x nivel (básico 1.0, avanzado 1.5, experto 2.0) |

Sobre el costo base se aplica el descuento de la reserva (máximo 50 %) y luego el impuesto configurado.

## Autor

Andrés Mauricio Arias Cortés - Grupo 213023_2204
