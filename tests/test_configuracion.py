import json

import pytest

from app.configuracion import cargar_configuracion
from app.excepciones import ErrorConfiguracion


def _config_base(dbc_path: str) -> dict:
    return {
        "aplicacion": {"ambiente": "PRODUCCION", "empresa": "EMP64"},
        "foxpro": {
            "dbc": dbc_path,
            "provider": "VFPOLEDB.1",
            "collating_sequence": "Machine",
        },
        "sql_server": {
            "servidor": "SRVERPQYPN\\SQLEXPRESS",
            "base_datos": "IntegracionSAIEmp64",
            "driver": "ODBC Driver 18 for SQL Server",
            "autenticacion_windows": True,
            "encrypt": True,
            "trust_server_certificate": True,
        },
        "sincronizacion": {
            "lugar": "GENERAL",
            "agentes": [3101, 3102, 3103, 3104],
            "fecha_inicial": "2026-08-01",
            "ventana_dias": 4,
        },
        "reintentos": {"maximos": 4, "espera_segundos": 30},
    }


def _escribir_config(tmp_path, datos: dict):
    ruta = tmp_path / "config.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return ruta


def test_configuracion_valida(tmp_path):
    dbc = tmp_path / "EMP64" / "sai.DBC"
    dbc.parent.mkdir(parents=True)
    dbc.write_text("x")

    ruta = _escribir_config(tmp_path, _config_base(str(dbc)))
    cfg = cargar_configuracion(ruta)

    assert cfg.empresa == "EMP64"
    assert cfg.agentes == (3101, 3102, 3103, 3104)


def test_falla_si_dbc_no_corresponde_a_empresa(tmp_path):
    dbc = tmp_path / "OTRA" / "sai.DBC"
    dbc.parent.mkdir(parents=True)
    dbc.write_text("x")

    ruta = _escribir_config(tmp_path, _config_base(str(dbc)))
    with pytest.raises(ErrorConfiguracion):
        cargar_configuracion(ruta)


def test_falla_si_no_existe_el_dbc(tmp_path):
    dbc_inexistente = tmp_path / "EMP64" / "sai.DBC"
    ruta = _escribir_config(tmp_path, _config_base(str(dbc_inexistente)))
    with pytest.raises(ErrorConfiguracion):
        cargar_configuracion(ruta)


def test_falla_si_autenticacion_windows_es_false(tmp_path):
    dbc = tmp_path / "EMP64" / "sai.DBC"
    dbc.parent.mkdir(parents=True)
    dbc.write_text("x")

    datos = _config_base(str(dbc))
    datos["sql_server"]["autenticacion_windows"] = False
    ruta = _escribir_config(tmp_path, datos)

    with pytest.raises(ErrorConfiguracion):
        cargar_configuracion(ruta)


def test_falla_si_lista_de_agentes_vacia(tmp_path):
    dbc = tmp_path / "EMP64" / "sai.DBC"
    dbc.parent.mkdir(parents=True)
    dbc.write_text("x")

    datos = _config_base(str(dbc))
    datos["sincronizacion"]["agentes"] = []
    ruta = _escribir_config(tmp_path, datos)

    with pytest.raises(ErrorConfiguracion):
        cargar_configuracion(ruta)
