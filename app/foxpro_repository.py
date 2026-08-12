from __future__ import annotations
from datetime import date
from typing import Any, List, Tuple
from .excepciones import ErrorConexionFoxPro, ErrorConsultaFoxPro
from .modelos import ConfiguracionAplicacion

class FoxProRepository:
    """
    Repositorio de extracción. Nunca realiza INSERT/UPDATE/DELETE/PACK
    sobre los archivos DBF.
    """

    def __init__(self, cfg: ConfiguracionAplicacion):
        self.cfg = cfg

    def _cadena_conexion(self) -> str:
        # "Exclusive=No;BackgroundFetch=No;" es la cadena que se validó como 
        # exitosa en las pruebas de conectividad (punto 7 del análisis de planeación).
        return (
            f"Provider={self.cfg.provider};"
            f"Data Source={self.cfg.dbc};"
            f"Collating Sequence={self.cfg.collating_sequence};"
            f"Exclusive=No;"
            f"BackgroundFetch=No;"
            f"Null=Yes;"
            f"Deleted=Yes;"
        )

    def _abrir_conexion(self):
        try:
            import pythoncom
            import adodbapi

            pythoncom.CoInitialize()  
            return adodbapi.connect(self._cadena_conexion())
        except Exception as e:
            raise ErrorConexionFoxPro(
                "No fue posible abrir la conexión "
                f"FoxPro para {self.cfg.dbc}: {e}"
            ) from e

    @staticmethod
    def es_transitorio(exc: Exception) -> bool:
        """Determina si el error es susceptible de reintento.
        No se utilizo "access denied" en esta lista. Un error de
        permisos casi siempre es permanente, no transitorio y solo
        retrasa 90 segundos un fallo que de todos modos va a ocurrir.
        """
        texto_error = " ".join(
            str(elemento)
            for elemento in _recorrer_excepciones(exc)
        ).lower()

        indicadores = (
            "locked",
            "ocupado",
            "temporarily",
            "temporalmente",
            "sharing violation",
            "network",
            "timeout",
            "could not be locked",
            "file is in use",
            "connection failure",
        )
        return any(indicador in texto_error for indicador in indicadores)

    def extraer(self, fecha_desde: date) -> List[Tuple[Any, ...]]:
        """
        Extrae pedidos que cumplen los filtros de negocio.
        Devuelve lista de tuplas en el orden de columnas esperado por normalizacion.
        """
        if not self.cfg.agentes:
            raise ErrorConsultaFoxPro(
                "No hay agentes configurados para la extracción."
            )
        conn = None
        cur = None
        try:
            conn = self._abrir_conexion()
            cur = conn.cursor()

            placeholders_agentes = " OR ".join(
                ["cve_age = ?" for _ in self.cfg.agentes]
            )
            sql = f"""
                SELECT
                    no_ped,
                    cve_suc,
                    lugar,
                    hora_ped,
                    status,
                    status2,
                    f_alta_ped,
                    fecha_ent,
                    cve_age,
                    cve_cte,
                    subt_ped,
                    cvede4,
                    cvede5
                FROM pedidoc
                WHERE lugar = ?
                  AND ({placeholders_agentes})
                  AND f_alta_ped >= ?
            """
            parametros = (
                self.cfg.lugar,
                *self.cfg.agentes,
                fecha_desde,
            )
            cur.execute(sql, parametros)
            filas = cur.fetchall()

            if filas is None:
                # raise ErrorConsultaFoxPro(
                #     "La consulta FoxPro no devolvió resultados."
                # )
                return []
            return [
                tuple(fila)
                for fila in filas
            ]
        except ErrorConexionFoxPro:
            raise
        except Exception as e:
            raise ErrorConsultaFoxPro(
                "Falló la consulta de pedidos en FoxPro: "
                f"{e}"
            ) from e

        finally:
            if cur is not None:
                try:
                    cur.close()
                except Exception:
                    pass
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

def _recorrer_excepciones(exc: BaseException) -> list[BaseException]:
    """Recorre recursivamente la excepción, sus causas, contextos y argumentos internos."""
    resultado: list[BaseException] = []
    actual: BaseException | None = exc
    visitados: set[int] = set()

    while actual is not None and id(actual) not in visitados:
        visitados.add(id(actual))
        resultado.append(actual)
        
        # Extraer argumentos si existen (común en errores COM/adodbapi)
        if hasattr(actual, "args") and actual.args:
            for arg in actual.args:
                if isinstance(arg, BaseException) and id(arg) not in visitados:
                    resultado.append(arg)

        # Avanzar a la causa o contexto explícito
        actual = actual.__cause__ or actual.__context__

    return resultado