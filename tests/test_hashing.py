from datetime import date, time
from decimal import Decimal
from app.hashing import agregar_hash, canonico
from app.modelos import Pedido

def _pedido_ejemplo() -> Pedido:
    return Pedido(
        no_pedido=Decimal(10025),
        clave_sucursal="001",
        lugar="GENERAL",
        hora_pedido=time(11, 59),
        estatus="ABIERTO",
        estatus2="SURTIDO",
        fecha_alta_pedido=date(2026, 8, 10),
        fecha_entrega=date(2026, 8, 12),
        clave_agente=Decimal(3101),
        clave_cliente=Decimal(500),
        subtotal_pedido=Decimal("1250.500000"),
        clave_vendedor4=Decimal(3101),
        clave_vendedor5=Decimal(3102),
    )

def test_hash_tiene_32_bytes():
    p = agregar_hash(_pedido_ejemplo())
    assert len(p.hash_origen) == 32
    assert isinstance(p.hash_origen, bytes)

def test_canonico_estable():
    c = canonico(_pedido_ejemplo())
    assert c.startswith("v1.0|10025|001|GENERAL|11:59:00|")
    assert c.endswith("1250.500000|3101|3102")

def test_mismo_pedido_mismo_hash():
    a = agregar_hash(_pedido_ejemplo())
    b = agregar_hash(_pedido_ejemplo())
    assert a.hash_origen == b.hash_origen

def test_pedido_distinto_hash_distinto():
    from dataclasses import replace

    a = agregar_hash(_pedido_ejemplo())
    modificado = replace(_pedido_ejemplo(), estatus="CANCELADO")
    b = agregar_hash(modificado)
    assert a.hash_origen != b.hash_origen