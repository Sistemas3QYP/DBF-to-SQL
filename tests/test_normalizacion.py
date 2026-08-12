from datetime import time
import pytest
from app.excepciones import ErrorValidacionDatos
from app.normalizacion import hora, texto, fecha, dec

@pytest.mark.parametrize(
    "valor, esperado",
    [
        (1159, time(11, 59)),
        ("1159", time(11, 59)),
        ("11:59", time(11, 59)),
        ("01:05", time(1, 5)),
        (0, None),
        ("", None),
        (None, None),
        ("0000", None),
        (2400, time(0, 0)),
        (time(8, 30, 15), time(8, 30)),
    ],
)
def test_hora_valida(valor, esperado):
    assert hora(valor) == esperado

@pytest.mark.parametrize("valor", [2460, 1265, 9999, 2500, -1, "ab"])
def test_hora_invalida(valor):
    with pytest.raises(ErrorValidacionDatos):
        hora(valor)

def test_texto_mayusculas_y_longitud():
    assert texto("  general ", 10) == "GENERAL"
    with pytest.raises(ErrorValidacionDatos):
        texto("", 5)
    with pytest.raises(ErrorValidacionDatos):
        texto("ABCDEFGHIJK", 5)

def test_fecha_obligatoria():
    from datetime import date
    assert fecha("2026-08-01", True) == date(2026, 8, 1)
    with pytest.raises(ErrorValidacionDatos):
        fecha(None, True)

def test_decimal():
    from decimal import Decimal
    assert dec("1250.5", 19, 6) == Decimal("1250.500000")
    assert dec(3101, 5, 0) == Decimal("3101")
    with pytest.raises(ErrorValidacionDatos):
        dec("abc", 5, 0)

def test_decimal_obligatorio_vacio_falla():
    with pytest.raises(ErrorValidacionDatos):
        dec(None, 10, 0, obligatorio=True)
    with pytest.raises(ErrorValidacionDatos):
        dec("", 10, 0, obligatorio=True)

def test_decimal_opcional_vacio_es_cero():
    from decimal import Decimal
    assert dec(None, 19, 6, obligatorio=False) == Decimal("0.000000")

def test_decimal_cero_explicito_no_falla_si_obligatorio():
    # Un 0 explícito (p.ej. subtotal de $0.00) es válido; solo se rechaza
    # la AUSENCIA de valor, no el valor 0 en sí.
    from decimal import Decimal

    assert dec(0, 19, 6, obligatorio=True) == Decimal("0.000000")