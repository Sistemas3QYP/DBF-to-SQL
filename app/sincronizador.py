from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from .excepciones import (
    ErrorCargaStaging,
    ErrorConexionFoxPro,
    ErrorConexionSQL,
    ErrorConsultaFoxPro,
    ErrorSincronizacionSQL,
    ErrorValidacionDatos,
)
from .hashing import agregar_hash
from .modelos import (
    ConfiguracionAplicacion,
    ResultadoSincronizacion,
)
from .normalizacion import (
    normalizar_pedido,
    validar_lote,
)
from .reintentos import ejecutar_con_reintentos


class Sincronizador:
    def __init__(
        self,
        cfg: ConfiguracionAplicacion,
        fox,
        sql,
        logger,
    ):
        self.cfg = cfg
        self.fox = fox
        self.sql = sql
        self.log = logger

    def ejecutar(
        self,
        id_ejecucion: UUID,
    ) -> ResultadoSincronizacion:

        hoy = date.today()

        es_inicial = not self.sql.hay_ejecucion_completada()

        fecha_desde = (
            self.cfg.fecha_inicial
            if es_inicial
            else max(
                self.cfg.fecha_inicial,
                hoy - timedelta(
                    days=self.cfg.ventana_dias
                ),
            )
        )

        tipo = (
            "INICIAL"
            if es_inicial
            else "INCREMENTAL"
        )

        self.log.info(
            "Iniciando ejecución %s | tipo=%s | desde=%s",
            id_ejecucion,
            tipo,
            fecha_desde,
        )

        try:
            self.sql.iniciar(
                id_ejecucion,
                fecha_desde,
                tipo,
            )

        except ErrorConexionSQL:
            self.log.exception(
                "No fue posible registrar inicio en bitácora SQL"
            )
            raise

        intentos = 1
        extraidos = 0
        insertados = 0
        actualizados = 0

        try:
            filas, intentos = ejecutar_con_reintentos(
                lambda: self.fox.extraer(
                    fecha_desde
                ),
                self.cfg.reintentos_maximos,
                self.cfg.espera_segundos,
                self.fox.es_transitorio,
                self.log,
            )

            extraidos = len(filas)

            if not filas:
                self.sql.finalizar(
                    id_ejecucion,
                    estado="SIN_REGISTROS",
                    extraidos=0,
                    insertados=0,
                    actualizados=0,
                    intentos=intentos,
                )

                self.log.info(
                    "Sin registros que cumplan los filtros"
                )

                return ResultadoSincronizacion(
                    intentos=intentos,
                    estado="SIN_REGISTROS",
                )

            self.log.info(
                "Extraídos %s registros de FoxPro",
                extraidos,
            )

            pedidos = [
                agregar_hash(
                    normalizar_pedido(
                        tuple(fila)
                    )
                )
                for fila in filas
            ]

            validar_lote(
                pedidos,
                self.cfg.lugar,
                self.cfg.agentes,
            )

            self.sql.cargar_staging(
                id_ejecucion,
                pedidos,
            )

            (
                insertados,
                actualizados,
                observados_sin_cambios,
            ) = self.sql.sincronizar(
                id_ejecucion
            )

            self.log.info(
                "Sincronización completada | "
                "insertados=%s | "
                "actualizados=%s | "
                "observados=%s",
                insertados,
                actualizados,
                observados_sin_cambios,
            )

            self.sql.finalizar(
                id_ejecucion,
                estado="COMPLETADA",
                extraidos=extraidos,
                insertados=insertados,
                actualizados=actualizados,
                intentos=intentos,
            )

            return ResultadoSincronizacion(
                extraidos=extraidos,
                insertados=insertados,
                actualizados=actualizados,
                intentos=intentos,
                estado="COMPLETADA",
            )

        except Exception as e:

            if isinstance(
                e,
                (
                    ErrorConexionSQL,
                    ErrorCargaStaging,
                    ErrorSincronizacionSQL,
                ),
            ):
                estado_error = "ERROR_SQL"

            elif isinstance(
                e,
                (
                    ErrorConexionFoxPro,
                    ErrorConsultaFoxPro,
                ),
            ):
                estado_error = "ERROR_FOXPRO"

            elif isinstance(
                e,
                ErrorValidacionDatos,
            ):
                estado_error = "ERROR_VALIDACION"

            else:
                estado_error = "ERROR_GENERAL"

            mensaje_error = str(e)[:4000]

            try:
                self.sql.finalizar(
                    id_ejecucion,
                    estado=estado_error,
                    extraidos=extraidos,
                    insertados=insertados,
                    actualizados=actualizados,
                    intentos=intentos,
                    error=mensaje_error,
                )

            except Exception:
                self.log.exception(
                    "No fue posible actualizar la bitácora con el error"
                )

            raise