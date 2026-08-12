from __future__ import annotations
import hashlib
from dataclasses import replace
from .modelos import Pedido

def canonico(p: Pedido) -> str:
    # Nota: se usa "|" como separador. 
    vals = [
        "v1.0",
        format(p.no_pedido, ".0f"), # decimal(10,0)
        p.clave_sucursal,
        p.lugar,
        p.hora_pedido.isoformat() if p.hora_pedido else "",
        p.estatus,
        p.estatus2,
        p.fecha_alta_pedido.isoformat(),
        p.fecha_entrega.isoformat() if p.fecha_entrega else "",
        format(p.clave_agente, ".0f"), # decimal(5,0)
        format(p.clave_cliente, ".0f"), # decimal(5,0)
        format(p.subtotal_pedido, ".6f"), # decimal(19,6)
        format(p.clave_vendedor4, ".0f"), # decimal(5,0)
        format(p.clave_vendedor5, ".0f"), # decimal(5,0)
    ]
    return "|".join(vals)

def agregar_hash(p: Pedido) -> Pedido:
    """Devuelve un nuevo Pedido con hash_origen (32 bytes) calculado."""
    digest = hashlib.sha256(canonico(p).encode("utf-8")).digest()
    return replace(p, hash_origen=digest)
