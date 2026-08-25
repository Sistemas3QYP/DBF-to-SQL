from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ConfiguracionAplicacion:
    ambiente: str
    empresa: str
    dbc: Path
    provider: str
    collating_sequence: str
    sql_servidor: str
    sql_base_datos: str
    sql_driver: str
    autenticacion_windows: bool
    encrypt: bool
    trust_server_certificate: bool
    lugar: str
    agentes: tuple[int, ...]
    fecha_inicial: date
    ventana_dias: int
    reintentos_maximos: int
    espera_segundos: int
    tamano_lote: int
    lock_max_minutos: int
    retencion_staging_dias: int


@dataclass(frozen=True, slots=True)
class Pedido:
    no_pedido: Decimal
    clave_sucursal: str
    lugar: str
    hora_pedido: time | None
    estatus: str
    estatus2: str
    fecha_alta_pedido: date
    clave_agente: Decimal
    clave_cliente: Decimal
    hash_origen: bytes = b""


@dataclass(frozen=True, slots=True)
class FacturaPedido:
    no_pedido: Decimal
    clave_sucursal: str
    no_factura: str
    fecha_factura: date
    hora_factura: time | None


@dataclass(frozen=True, slots=True)
class ResultadoSincronizacion:
    extraidos: int = 0
    insertados: int = 0
    actualizados: int = 0
    facturas_extraidas: int = 0
    facturas_actualizadas: int = 0
    facturas_sin_cambios: int = 0
    facturas_sin_pedido: int = 0
    intentos: int = 1
    estado: str = "COMPLETADA"