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
    consolidar_facturas,
    normalizar_factura_pedido,
    normalizar_pedido,
    validar_lote,
    validar_lote_facturas,
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

        es_inicial = (
            not self.sql.hay_ejecucion_completada()
        )

        fecha_desde_pedidos = (
            self.cfg.fecha_inicial
            if es_inicial
            else max(
                self.cfg.fecha_inicial,
                hoy - timedelta(
                    days=self.cfg.ventana_dias
                ),
            )
        )

        # El proceso de facturación usa una ventana propia basada en
        # falta_fac. Para la primera ejecución general se utiliza la
        # fecha inicial; en posteriores ejecuciones se usan cuatro días.
        
        fecha_desde_facturas = (
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
            "Iniciando ejecución %s | tipo=%s | "
            "pedidos_desde=%s | facturas_desde=%s",
            id_ejecucion,
            tipo,
            fecha_desde_pedidos,
            fecha_desde_facturas,
        )

        try:
            self.sql.iniciar(
                id_ejecucion,
                fecha_desde_pedidos,
                tipo,
            )

        except ErrorConexionSQL:
            self.log.exception(
                "No fue posible registrar inicio "
                "en bitácora SQL."
            )
            raise

        intentos = 1
        extraidos = 0
        insertados = 0
        actualizados_pedidos = 0
        facturas_extraidas = 0
        facturas_actualizadas = 0
        facturas_sin_cambios = 0
        facturas_sin_pedido = 0

        try:
            # PROCESO A: SINCRONIZACIÓN DE PEDIDOS
            filas_pedidos, intentos_pedidos = (
                ejecutar_con_reintentos(
                    lambda: self.fox.extraer(
                        fecha_desde_pedidos
                    ),
                    self.cfg.reintentos_maximos,
                    self.cfg.espera_segundos,
                    self.fox.es_transitorio,
                    self.log,
                )
            )

            intentos = max(
                intentos,
                intentos_pedidos,
            )

            extraidos = len(filas_pedidos)

            if filas_pedidos:
                self.log.info(
                    "Extraídos %s pedidos de FoxPro.",
                    extraidos,
                )

                pedidos = [
                    agregar_hash(
                        normalizar_pedido(
                            tuple(fila)
                        )
                    )
                    for fila in filas_pedidos
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
                    actualizados_pedidos,
                    observados_sin_cambios,
                ) = self.sql.sincronizar(
                    id_ejecucion
                )

                self.log.info(
                    "Pedidos sincronizados | "
                    "insertados=%s | actualizados=%s | "
                    "observados=%s",
                    insertados,
                    actualizados_pedidos,
                    observados_sin_cambios,
                )

            else:
                self.log.info(
                    "No se encontraron pedidos recientes. "
                    "Se continuará con facturación."
                )

            # =====================================================
            # PROCESO B: ENRIQUECIMIENTO DE FACTURACIÓN
            # =====================================================

            filas_facturas, intentos_facturas = (
                ejecutar_con_reintentos(
                    lambda: self.fox.extraer_facturas(
                        fecha_desde_facturas
                    ),
                    self.cfg.reintentos_maximos,
                    self.cfg.espera_segundos,
                    self.fox.es_transitorio,
                    self.log,
                )
            )

            intentos = max(
                intentos,
                intentos_facturas,
            )

            facturas_extraidas = len(
                filas_facturas
            )

            if filas_facturas:
                self.log.info(
                    "Extraídas %s relaciones de "
                    "facturación de FoxPro.",
                    facturas_extraidas,
                )

                facturas_normalizadas = [
                    normalizar_factura_pedido(
                        tuple(fila)
                    )
                    for fila in filas_facturas
                ]

                facturas = consolidar_facturas(
                    facturas_normalizadas
                )

                validar_lote_facturas(
                    facturas
                )

                self.log.info(
                    "Facturas consolidadas | "
                    "origen=%s | pedidos_unicos=%s",
                    facturas_extraidas,
                    len(facturas),
                )

                self.sql.cargar_staging_facturas(
                    id_ejecucion,
                    facturas,
                )

                (
                    facturas_actualizadas,
                    facturas_sin_cambios,
                    facturas_sin_pedido,
                ) = self.sql.sincronizar_facturas(
                    id_ejecucion
                )

                self.log.info(
                    "Facturación sincronizada | "
                    "actualizadas=%s | sin_cambios=%s | "
                    "sin_pedido=%s",
                    facturas_actualizadas,
                    facturas_sin_cambios,
                    facturas_sin_pedido,
                )

            else:
                self.log.info(
                    "No se encontraron facturas recientes."
                )

            actualizados_totales = (
                actualizados_pedidos
                + facturas_actualizadas
            )

            estado = (
                "SIN_REGISTROS"
                if extraidos == 0
                and facturas_extraidas == 0
                else "COMPLETADA"
            )

            self.sql.finalizar(
                id_ejecucion,
                estado=estado,
                extraidos=(
                    extraidos
                    + facturas_extraidas
                ),
                insertados=insertados,
                actualizados=actualizados_totales,
                intentos=intentos,
            )

            return ResultadoSincronizacion(
                extraidos=extraidos,
                insertados=insertados,
                actualizados=actualizados_pedidos,
                facturas_extraidas=(
                    facturas_extraidas
                ),
                facturas_actualizadas=(
                    facturas_actualizadas
                ),
                facturas_sin_cambios=(
                    facturas_sin_cambios
                ),
                facturas_sin_pedido=(
                    facturas_sin_pedido
                ),
                intentos=intentos,
                estado=estado,
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
                    extraidos=(
                        extraidos
                        + facturas_extraidas
                    ),
                    insertados=insertados,
                    actualizados=(
                        actualizados_pedidos
                        + facturas_actualizadas
                    ),
                    intentos=intentos,
                    error=mensaje_error,
                )

            except Exception:
                self.log.exception(
                    "No fue posible actualizar la "
                    "bitácora con el error."
                )

            raise