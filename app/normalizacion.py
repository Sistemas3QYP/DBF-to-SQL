from __future__ import annotations
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Collection, Literal, overload
import math
from .excepciones import ErrorValidacionDatos
from .modelos import FacturaPedido, Pedido


def texto(v: Any, maximo: int, obligatorio: bool = True) -> str:
    x = "" if v is None else str(v).strip().upper()

    if obligatorio and not x:
        raise ErrorValidacionDatos("Cadena obligatoria vacía")
    if "\x00" in x:
        raise ErrorValidacionDatos("La cadena contiene caracteres nulos.")
    if len(x) > maximo:
        raise ErrorValidacionDatos(f"Cadena excede longitud máxima {maximo}: {x[:50]}")
    return x


@overload
def fecha(v: Any, *, obligatoria: Literal[True]) -> date: ...


@overload
def fecha(
    v: Any,
    *,
    obligatoria: Literal[False] = False,
) -> date | None: ...


def fecha(v: Any, obligatoria: bool = False) -> date | None:
    if v is None or v == "":
        if obligatoria:
            raise ErrorValidacionDatos("Fecha obligatoria vacía")
        return None
    if isinstance(v, bool):
        raise ErrorValidacionDatos(f"fecha inválida: {v}")
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v

    valor = str(v).strip()

    if not valor:
        if obligatoria:
            raise ErrorValidacionDatos("Fecha obligatoria vacía")
        return None

    try:
        return date.fromisoformat(valor[:10])
    except ValueError as e:
        raise ErrorValidacionDatos(f"Fecha inválida: {v}") from e


def hora(v: Any) -> time | None:
    """
    Normaliza hora_ped de FoxPro a datetime.time.
    Acepta: time, datetime, enteros tipo 1159, cadenas "11:59", "1159", 0, vacío.
    Rechaza valores imposibles (2460, 1265, 9999, etc.).
    """
    if v is None:
        return None
    if isinstance(v, bool):
        raise ErrorValidacionDatos(f"Hora inválida: {v}")
    if isinstance(v, time):
        return v.replace(second=0, microsecond=0)
    if isinstance(v, datetime):
        return v.time().replace(second=0, microsecond=0)

    valor = str(v).strip()

    if valor in {"", "0", "0000", "00:00", "00:00:00"}:
        return None

    if ":" in valor:
        try:
            return time.fromisoformat(valor).replace(second=0, microsecond=0)
        except ValueError as e:
            raise ErrorValidacionDatos(f"Hora inválida: {v}") from e
        
    s = valor.replace(":", "")
    try:
        n = int(float(s))
    except (ValueError, TypeError) as e:
        raise ErrorValidacionDatos(f"Hora inválida: {v}") from e

    if n == 2400:
        return time(0, 0)

    h, m = divmod(n, 100)

    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ErrorValidacionDatos(f"Hora inválida: {v}")

    return time(h, m)


def dec(v: Any, precision: int, escala: int = 0, obligatorio: bool = False) -> Decimal:
    if precision < 1:
        raise ValueError("precision debe ser mayor que cero.")

    if escala < 0 or escala > precision:
        raise ValueError("escala debe estar entre cero y precision.")

    if isinstance(v, bool):
        raise ErrorValidacionDatos(f"Decimal inválido: {v}")

    vacio = v is None or v == ""
    if vacio:
        if obligatorio:
            raise ErrorValidacionDatos("Valor numérico obligatorio vacío")
        v = 0

    try:
        if isinstance(v, Decimal):
            x = v
        elif isinstance(v, int):
            x = Decimal(v)
        elif isinstance(v, float):
            if not math.isfinite(v):
                raise ErrorValidacionDatos(f"Decimal no finito: {v}")
            # repr evita pérdida de precisión típica de str(float)
            x = Decimal(repr(v))
        else:
            x = Decimal(str(v).strip())

        if not x.is_finite():
            raise ErrorValidacionDatos(f"Decimal no finito: {v}")

        quant = Decimal(1).scaleb(-escala)
        x = x.quantize(
            quant,
            rounding=ROUND_HALF_UP,
        )

    except ErrorValidacionDatos:
        raise
    except (InvalidOperation, ValueError) as e:
        raise ErrorValidacionDatos(f"Decimal inválido: {v}") from e

    max_enteros = precision - escala

    parte_entera = format(
        abs(x),
        "f",
    ).split(
        ".", maxsplit=1
    )[0]

    if len(parte_entera) > max_enteros:
        raise ErrorValidacionDatos(
            f"Decimal fuera de rango " f"({precision},{escala}): {x}"
        )

    return x


def normalizar_pedido(
    fila: tuple[Any, ...],
) -> Pedido:
    """
    Convierte una fila cruda de FoxPro (9 columnas) en un Pedido normalizado.
    Orden esperado:
      no_ped, cve_suc, lugar, hora_ped, status, status2,
      f_alta_ped, cve_age, cve_cte
    """
    if len(fila) != 9:
        raise ErrorValidacionDatos(
            f"Se esperaban exactamente 9 columnas de pedido, pero se recibieron: {len(fila)}"
        )

    pedido = Pedido(
        # no_pedido y clave_agente son llaves/filtros de negocio: obligatorios.
        no_pedido=dec(fila[0], 10, 0, obligatorio=True),
        clave_sucursal=texto(fila[1], 3),
        lugar=texto(fila[2], 10),
        hora_pedido=hora(fila[3]),
        estatus=texto(fila[4], 15),
        estatus2=texto(fila[5], 15),
        fecha_alta_pedido=fecha(fila[6], obligatoria=True),
        clave_agente=dec(fila[7], 5, 0, obligatorio=True),
        clave_cliente=dec(fila[8], 5, 0, obligatorio=True),
    )

    _validar_no_negativos(pedido)
    return pedido


def normalizar_factura_pedido(
    fila: tuple[Any, ...],
) -> FacturaPedido:
    """
    Convierte una fila de facturación en FacturaPedido.

    Orden esperado:
        no_ped,
        cve_suc,
        no_fac,
        falta_fac,
        hora_fac
    """

    if len(fila) != 5:
        raise ErrorValidacionDatos(
            "Se esperaban exactamente 5 columnas de facturación, "
            f"pero se recibieron: {len(fila)}"
        )

    no_pedido = dec(
        fila[0],
        10,
        0,
        obligatorio=True,
    )

    clave_sucursal = texto(
        fila[1],
        3,
    )

    no_factura = texto(
        fila[2],
        10,
    )

    fecha_factura = fecha(
        fila[3],
        obligatoria=True,
    )

    hora_factura = hora(
        fila[4],
    )

    if no_pedido <= 0:
        raise ErrorValidacionDatos(
            f"NoPedido de factura debe ser positivo: {no_pedido}"
        )

    return FacturaPedido(
        no_pedido=no_pedido,
        clave_sucursal=clave_sucursal,
        no_factura=no_factura,
        fecha_factura=fecha_factura,
        hora_factura=hora_factura,
    )


def consolidar_facturas(
    facturas: list[FacturaPedido],
) -> list[FacturaPedido]:
    """
    Conserva una factura por pedido y sucursal.

    Si existen varias facturas para el mismo pedido, conserva:
    1. La de mayor FechaFactura.
    2. La de mayor HoraFactura.
    3. La de mayor NoFactura.
    """

    seleccionadas: dict[
        tuple[Decimal, str],
        FacturaPedido,
    ] = {}

    for factura in facturas:
        llave = (
            factura.no_pedido,
            factura.clave_sucursal,
        )

        actual = seleccionadas.get(llave)

        if actual is None:
            seleccionadas[llave] = factura
            continue

        if _clave_orden_factura(
            factura
        ) > _clave_orden_factura(actual):
            seleccionadas[llave] = factura

    return sorted(
        seleccionadas.values(),
        key=lambda factura: (
            factura.no_pedido,
            factura.clave_sucursal,
        ),
    )


def validar_lote_facturas(
    facturas: list[FacturaPedido],
) -> None:
    """Valida el lote consolidado de facturas."""

    vistos: set[tuple[Decimal, str]] = set()

    for factura in facturas:
        llave = (
            factura.no_pedido,
            factura.clave_sucursal,
        )

        if llave in vistos:
            raise ErrorValidacionDatos(
                "Llave de factura duplicada después de consolidar: "
                f"{llave}"
            )

        vistos.add(llave)

        if not factura.no_factura:
            raise ErrorValidacionDatos(
                f"NoFactura vacío para el pedido {llave}"
            )

        if len(factura.no_factura) > 10:
            raise ErrorValidacionDatos(
                "NoFactura excede diez caracteres: "
                f"{factura.no_factura}"
            )


def _clave_orden_factura(
    factura: FacturaPedido,
) -> tuple[date, time, str]:
    hora_orden = (
        factura.hora_factura
        if factura.hora_factura is not None
        else time.min
    )

    return (
        factura.fecha_factura,
        hora_orden,
        factura.no_factura,
    )


def validar_lote(
    pedidos: list[Pedido],
    lugar_esperado: str,
    agentes_permitidos: Collection[int],
) -> None:
    """
    Valida lote de pedidos antes de cargarlo en staging:
    - Sin llaves duplicadas - NoPed válido - Lugar esperado - Agente permitido
    - Todos los registros cumplen filtros de negocio
    """
    lugar_esperado = lugar_esperado.strip().upper()
    agentes = set(agentes_permitidos)
    vistos: set[tuple[Decimal, str]] = set()

    for p in pedidos:
        llave = (p.no_pedido, p.clave_sucursal)
        if llave in vistos:
            raise ErrorValidacionDatos(f"Llave duplicada en el lote: {llave}")

        vistos.add(llave)

        if p.no_pedido <= 0:
            raise ErrorValidacionDatos(f"no_pedido debe ser positivo: {llave}")
        
        if p.lugar != lugar_esperado:
            raise ErrorValidacionDatos(
                f"Registro con lugar distinto de {lugar_esperado}: {llave}"
            )
        if int(p.clave_agente) not in agentes:
            raise ErrorValidacionDatos(
                f"Agente no permitido ({p.clave_agente}) en pedido {llave}"
            )

        if len(p.hash_origen) != 32:
            raise ErrorValidacionDatos(f"Hash inválido en pedido {llave}.")


def _validar_no_negativos(p: Pedido) -> None:
    campos = {
        "no_pedido": p.no_pedido,
        "clave_agente": p.clave_agente,
        "clave_cliente": p.clave_cliente,
    }

    for nombre, valor in campos.items():
        if valor < 0:
            raise ErrorValidacionDatos(f"{nombre} no puede ser negativo: {valor}")