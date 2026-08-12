from __future__ import annotations
from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

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
    fecha_entrega: date | None
    clave_agente: Decimal
    clave_cliente: Decimal
    subtotal_pedido: Decimal
    clave_vendedor4: Decimal
    clave_vendedor5: Decimal
    hash_origen: bytes = b""

@dataclass(frozen=True, slots=True)
class ResultadoSincronizacion:
    extraidos: int = 0
    insertados: int = 0
    actualizados: int = 0
    intentos: int = 1
    estado: str = "COMPLETADA"