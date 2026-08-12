"""Carga y validación de la configuración JSON."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path, PureWindowsPath
from typing import Any, Mapping

from .excepciones import ErrorConfiguracion
from .modelos import ConfiguracionAplicacion

_EMPRESAS_SOPORTADAS = frozenset({"EMP43", "EMP64"})
_AMBIENTES_SOPORTADOS = frozenset({"PRUEBAS", "PRODUCCION"})
_PROVIDERS_SOPORTADOS = frozenset({"VFPOLEDB", "VFPOLEDB.1"})

def cargar_configuracion(
    ruta: str | Path,
) -> ConfiguracionAplicacion:
    """Lee y valida el archivo JSON de configuración."""

    p = Path(ruta).expanduser().resolve()

    if not p.is_file():
        raise ErrorConfiguracion(
            f"No existe el archivo de configuración: {p}"
        )

    try:
        contenido = p.read_text(encoding="utf-8-sig")
    except OSError as e:
        raise ErrorConfiguracion(
            f"No fue posible leer el archivo de configuración {p}: {e}"
        ) from e

    try:
        datos = json.loads(contenido)
    except json.JSONDecodeError as e:
        raise ErrorConfiguracion(
            "JSON inválido en "
            f"línea {e.lineno}, columna {e.colno}: {e.msg}"
        ) from e

    if not isinstance(datos, dict):
        raise ErrorConfiguracion(
            "La raíz de la configuración debe ser un objeto JSON."
        )

    try:
        aplicacion = _seccion(datos, "aplicacion")
        foxpro = _seccion(datos, "foxpro")
        sql_server = _seccion(datos, "sql_server")
        sincronizacion = _seccion(datos, "sincronizacion")
        reintentos = _seccion(datos, "reintentos")
        runtime = datos.get("runtime", {})

        if not isinstance(runtime, dict):
            raise ErrorConfiguracion(
                "La sección 'runtime' debe ser un objeto JSON."
            )

        cfg = ConfiguracionAplicacion(
            ambiente=_texto(aplicacion, "ambiente").upper(),
            empresa=_texto(aplicacion, "empresa").upper(),
            dbc=Path(_texto(foxpro, "dbc")),
            provider=_texto(foxpro, "provider"),
            collating_sequence=_texto_opcional(
                foxpro,
                "collating_sequence",
                "Machine",
            ),
            sql_servidor=_texto(sql_server, "servidor"),
            sql_base_datos=_texto(sql_server, "base_datos"),
            sql_driver=_texto(sql_server, "driver"),
            autenticacion_windows=_booleano(
                sql_server,
                "autenticacion_windows",
            ),
            encrypt=_booleano(sql_server, "encrypt"),
            trust_server_certificate=_booleano(
                sql_server,
                "trust_server_certificate",
            ),
            lugar=_texto(sincronizacion, "lugar").upper(),
            agentes=_agentes(sincronizacion.get("agentes")),
            fecha_inicial=_fecha_iso(
                _texto(sincronizacion, "fecha_inicial")
            ),
            ventana_dias=_entero(
                sincronizacion,
                "ventana_dias",
            ),
            reintentos_maximos=_entero(
                reintentos,
                "maximos",
            ),
            espera_segundos=_entero(
                reintentos,
                "espera_segundos",
            ),
            tamano_lote=_entero_opcional(
                sincronizacion,
                "tamano_lote",
                250,
            ),
            lock_max_minutos=_entero_opcional(
                runtime,
                "lock_max_minutos",
                60,
            ),
            retencion_staging_dias=_entero_opcional(
                sincronizacion,
                "retencion_staging_dias",
                7,
            ),
        )

    except ErrorConfiguracion:
        raise
    except (KeyError, TypeError, ValueError) as e:
        raise ErrorConfiguracion(
            f"Configuración incompleta o inválida: {e}"
        ) from e

    _validar_consistencia(cfg)
    return cfg


def _validar_consistencia(
    cfg: ConfiguracionAplicacion,
) -> None:
    """Valida reglas de seguridad entre empresa, DBC y SQL."""

    if cfg.empresa not in _EMPRESAS_SOPORTADAS:
        raise ErrorConfiguracion(
            f"Empresa no soportada: {cfg.empresa}"
        )

    if cfg.ambiente not in _AMBIENTES_SOPORTADOS:
        raise ErrorConfiguracion(
            f"Ambiente no soportado: {cfg.ambiente}"
        )

    partes_dbc = {
        parte.upper()
        for parte in PureWindowsPath(str(cfg.dbc)).parts
    }

    if cfg.empresa not in partes_dbc:
        raise ErrorConfiguracion(
            f"DBC no corresponde a {cfg.empresa}: {cfg.dbc}"
        )

    base_esperada = f"IntegracionSAI{cfg.empresa.title()}"

    if cfg.sql_base_datos.casefold() != base_esperada.casefold():
        raise ErrorConfiguracion(
            f"Base SQL esperada {base_esperada}, "
            f"recibida: {cfg.sql_base_datos}"
        )

    if cfg.dbc.suffix.casefold() != ".dbc":
        raise ErrorConfiguracion(
            f"La ruta no apunta a un archivo DBC: {cfg.dbc}"
        )

    if not cfg.dbc.is_file():
        raise ErrorConfiguracion(
            f"No existe el archivo DBC: {cfg.dbc}"
        )

    if cfg.provider.upper() not in _PROVIDERS_SOPORTADOS:
        raise ErrorConfiguracion(
            "Proveedor FoxPro no soportado. "
            "Use VFPOLEDB o VFPOLEDB.1."
        )

    if not cfg.autenticacion_windows:
        raise ErrorConfiguracion(
            "autenticacion_windows=false no está soportado. "
            "La integración utiliza Windows Authentication."
        )

    if cfg.lugar != "GENERAL":
        raise ErrorConfiguracion(
            "El lugar permitido para esta integración es GENERAL."
        )

    if not cfg.agentes:
        raise ErrorConfiguracion(
            "La lista de agentes no puede estar vacía."
        )

    if len(cfg.agentes) != len(set(cfg.agentes)):
        raise ErrorConfiguracion(
            "La lista de agentes contiene valores duplicados."
        )

    if any(agente <= 0 for agente in cfg.agentes):
        raise ErrorConfiguracion(
            "Todos los agentes deben ser enteros positivos."
        )

    if not 1 <= cfg.ventana_dias <= 30:
        raise ErrorConfiguracion(
            "ventana_dias debe estar entre 1 y 30 "
            f"(recibido: {cfg.ventana_dias})."
        )

    if not 1 <= cfg.reintentos_maximos <= 10:
        raise ErrorConfiguracion(
            "reintentos.maximos debe estar entre 1 y 10."
        )

    if not 0 <= cfg.espera_segundos <= 3600:
        raise ErrorConfiguracion(
            "espera_segundos debe estar entre 0 y 3600."
        )

    if not 1 <= cfg.tamano_lote <= 5000:
        raise ErrorConfiguracion(
            "tamano_lote debe estar entre 1 y 5000."
        )

    if not 5 <= cfg.lock_max_minutos <= 1440:
        raise ErrorConfiguracion(
            "lock_max_minutos debe estar entre 5 y 1440."
        )

    if not 1 <= cfg.retencion_staging_dias <= 365:
        raise ErrorConfiguracion(
            "retencion_staging_dias debe estar entre 1 y 365."
        )


def _seccion(
    datos: Mapping[str, Any],
    nombre: str,
) -> Mapping[str, Any]:
    valor = datos.get(nombre)

    if not isinstance(valor, dict):
        raise ErrorConfiguracion(
            f"Falta la sección obligatoria '{nombre}'."
        )

    return valor


def _texto(
    seccion: Mapping[str, Any],
    campo: str,
) -> str:
    valor = seccion.get(campo)

    if not isinstance(valor, str) or not valor.strip():
        raise ErrorConfiguracion(
            f"El campo '{campo}' debe ser texto no vacío."
        )

    if "\x00" in valor:
        raise ErrorConfiguracion(
            f"El campo '{campo}' contiene caracteres inválidos."
        )

    return valor.strip()


def _texto_opcional(
    seccion: Mapping[str, Any],
    campo: str,
    predeterminado: str,
) -> str:
    valor = seccion.get(campo, predeterminado)

    if not isinstance(valor, str) or not valor.strip():
        raise ErrorConfiguracion(
            f"El campo '{campo}' debe ser texto no vacío."
        )

    return valor.strip()


def _booleano(
    seccion: Mapping[str, Any],
    campo: str,
) -> bool:
    valor = seccion.get(campo)

    if type(valor) is not bool:
        raise ErrorConfiguracion(
            f"El campo '{campo}' debe ser true o false."
        )

    return valor


def _entero(
    seccion: Mapping[str, Any],
    campo: str,
) -> int:
    valor = seccion.get(campo)

    if type(valor) is not int:
        raise ErrorConfiguracion(
            f"El campo '{campo}' debe ser un entero."
        )

    return valor


def _entero_opcional(
    seccion: Mapping[str, Any],
    campo: str,
    predeterminado: int,
) -> int:
    valor = seccion.get(campo, predeterminado)

    if type(valor) is not int:
        raise ErrorConfiguracion(
            f"El campo '{campo}' debe ser un entero."
        )

    return valor


def _agentes(valor: Any) -> tuple[int, ...]:
    if not isinstance(valor, list) or not valor:
        raise ErrorConfiguracion(
            "El campo 'agentes' debe ser una lista no vacía."
        )

    if any(type(agente) is not int for agente in valor):
        raise ErrorConfiguracion(
            "Todos los agentes deben ser enteros."
        )

    return tuple(valor)


def _fecha_iso(valor: str) -> date:
    try:
        return date.fromisoformat(valor)
    except ValueError as e:
        raise ErrorConfiguracion(
            "fecha_inicial debe usar el formato AAAA-MM-DD."
        ) from e