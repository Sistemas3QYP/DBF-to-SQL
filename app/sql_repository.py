"""Repositorio para SQL Server."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from typing import Iterator
from uuid import UUID

from .excepciones import (
    ErrorCargaStaging,
    ErrorConexionSQL,
    ErrorSincronizacionSQL,
)
from .modelos import ConfiguracionAplicacion, Pedido

class SqlRepository:
    def __init__(
        self,
        cfg: ConfiguracionAplicacion,
    ):
        self.cfg = cfg

    def _cadena_conexion(self) -> str:
        encrypt = "yes" if self.cfg.encrypt else "no"
        trust = (
            "yes"
            if self.cfg.trust_server_certificate
            else "no"
        )

        return (
            f"DRIVER={{{self.cfg.sql_driver}}};"
            f"SERVER={self.cfg.sql_servidor};"
            f"DATABASE={self.cfg.sql_base_datos};"
            "Trusted_Connection=yes;"
            f"Encrypt={encrypt};"
            f"TrustServerCertificate={trust};"
            "APP=Integracion SAI;"
        )

    def conectar(self):
        try:
            import pyodbc

            return pyodbc.connect(
                self._cadena_conexion(),
                timeout=15,
                autocommit=False,
            )

        except Exception as e:
            raise ErrorConexionSQL(
                "No fue posible conectar con "
                f"{self.cfg.sql_servidor}/"
                f"{self.cfg.sql_base_datos}: {e}"
            ) from e

    @contextmanager
    def _conexion(self) -> Iterator:
        conn = self.conectar()

        try:
            yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def iniciar(
        self,
        id_ejecucion: UUID,
        fecha_desde: date,
        tipo: str,
    ) -> None:
        try:
            with self._conexion() as conn:
                cur = conn.cursor()

                try:
                    cur.execute(
                        """
                        INSERT INTO integracion.BitacoraEjecucion
                        (
                            IdEjecucion,
                            FechaInicio,
                            FechaDesdeFoxPro,
                            TipoEjecucion,
                            Estado,
                            NumeroIntentos
                        )
                        VALUES
                        (
                            ?,
                            SYSDATETIME(),
                            ?,
                            ?,
                            'INICIADA',
                            1
                        );
                        """,
                        (
                            id_ejecucion,
                            fecha_desde,
                            tipo,
                        ),
                    )
                    conn.commit()

                except Exception:
                    conn.rollback()
                    raise

                finally:
                    cur.close()

        except ErrorConexionSQL:
            raise
        except Exception as e:
            raise ErrorConexionSQL(
                f"No fue posible registrar el inicio: {e}"
            ) from e

    def finalizar(
        self,
        id_ejecucion: UUID,
        estado: str,
        extraidos: int = 0,
        insertados: int = 0,
        actualizados: int = 0,
        intentos: int = 1,
        error: str | None = None,
    ) -> None:
        try:
            with self._conexion() as conn:
                cur = conn.cursor()

                try:
                    cur.execute(
                        """
                        UPDATE integracion.BitacoraEjecucion
                        SET
                            FechaFin = SYSDATETIME(),
                            Estado = ?,
                            RegistrosExtraidos = ?,
                            RegistrosInsertados = ?,
                            RegistrosActualizados = ?,
                            NumeroIntentos = ?,
                            MensajeError = ?
                        WHERE IdEjecucion = ?;
                        """,
                        (
                            estado,
                            extraidos,
                            insertados,
                            actualizados,
                            intentos,
                            error,
                            id_ejecucion,
                        ),
                    )

                    if cur.rowcount != 1:
                        raise ErrorConexionSQL(
                            "No se encontró la ejecución "
                            f"{id_ejecucion} en la bitácora."
                        )

                    conn.commit()

                except Exception:
                    conn.rollback()
                    raise

                finally:
                    cur.close()

        except ErrorConexionSQL:
            raise
        except Exception as e:
            raise ErrorConexionSQL(
                f"No fue posible finalizar la bitácora: {e}"
            ) from e

    def cargar_staging(
        self,
        id_ejecucion: UUID,
        pedidos: list[Pedido],
    ) -> None:
        if not pedidos:
            return

        for pedido in pedidos:
            if len(pedido.hash_origen) != 32:
                raise ErrorCargaStaging(
                    "Se intentó cargar un pedido "
                    "con HashOrigen inválido."
                )

        try:
            with self._conexion() as conn:
                cur = conn.cursor()

                try:
                    cur.execute(
                        """
                        DELETE FROM integracion.PedidoSAI_Staging
                        WHERE IdEjecucion = ?;
                        """,
                        id_ejecucion,
                    )

                    cur.execute(
                        """
                        DELETE s
                        FROM integracion.PedidoSAI_Staging AS s
                        INNER JOIN integracion.BitacoraEjecucion AS b
                            ON b.IdEjecucion = s.IdEjecucion
                        WHERE b.Estado IN
                        (
                            'ERROR_SQL',
                            'ERROR_FOXPRO',
                            'ERROR_VALIDACION',
                            'ERROR_GENERAL'
                        )
                        AND b.FechaInicio < DATEADD
                        (
                            day,
                            -?,
                            SYSDATETIME()
                        );
                        """,
                        self.cfg.retencion_staging_dias,
                    )

                    sql_insert = """
                        INSERT INTO integracion.PedidoSAI_Staging
                        (
                            IdEjecucion,
                            NoPedido,
                            ClaveSucursal,
                            Lugar,
                            HoraPedido,
                            Estatus,
                            Estatus2,
                            FechaAltaPedido,
                            FechaEntrega,
                            ClaveAgente,
                            ClaveCliente,
                            SubtotalPedido,
                            ClaveVendedor4,
                            ClaveVendedor5,
                            HashOrigen
                        )
                        VALUES
                        (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?
                        );
                    """

                    filas = [
                        (
                            id_ejecucion,
                            p.no_pedido,
                            p.clave_sucursal,
                            p.lugar,
                            p.hora_pedido,
                            p.estatus,
                            p.estatus2,
                            p.fecha_alta_pedido,
                            p.fecha_entrega,
                            p.clave_agente,
                            p.clave_cliente,
                            p.subtotal_pedido,
                            p.clave_vendedor4,
                            p.clave_vendedor5,
                            p.hash_origen,
                        )
                        for p in pedidos
                    ]

                    cur.fast_executemany = True
                    tam = self.cfg.tamano_lote

                    for inicio in range(
                        0,
                        len(filas),
                        tam,
                    ):
                        lote = filas[
                            inicio:inicio + tam
                        ]

                        cur.executemany(
                            sql_insert,
                            lote,
                        )

                    conn.commit()

                except Exception:
                    conn.rollback()
                    raise

                finally:
                    cur.close()

        except ErrorConexionSQL:
            raise
        except ErrorCargaStaging:
            raise
        except Exception as e:
            raise ErrorCargaStaging(
                f"Falló la carga de staging: {e}"
            ) from e

    def sincronizar(
        self,
        id_ejecucion: UUID,
    ) -> tuple[int, int, int]:
        try:
            with self._conexion() as conn:
                cur = conn.cursor()

                try:
                    cur.execute(
                        """
                        EXEC integracion.SyncPedidosSAI
                            @IdEjecucion = ?;
                        """,
                        id_ejecucion,
                    )

                    fila = cur.fetchone()

                    if fila is None:
                        raise ErrorSincronizacionSQL(
                            "El procedimiento no devolvió resultados."
                        )

                    insertados = int(fila[0])
                    actualizados = int(fila[1])
                    observados = int(fila[2])

                    conn.commit()

                    return (
                        insertados,
                        actualizados,
                        observados,
                    )

                except Exception:
                    conn.rollback()
                    raise

                finally:
                    cur.close()

        except ErrorConexionSQL:
            raise
        except ErrorSincronizacionSQL:
            raise
        except Exception as e:
            raise ErrorSincronizacionSQL(
                f"Falló SyncPedidosSAI: {e}"
            ) from e

    def hay_ejecucion_completada(self) -> bool:
        try:
            with self._conexion() as conn:
                cur = conn.cursor()

                try:
                    cur.execute(
                        """
                        SELECT TOP (1) 1
                        FROM integracion.BitacoraEjecucion
                        WHERE Estado IN
                        (
                            'COMPLETADA',
                            'SIN_REGISTROS'
                        )
                        ORDER BY FechaInicio DESC;
                        """
                    )

                    return cur.fetchone() is not None

                finally:
                    cur.close()

        except ErrorConexionSQL:
            raise
        except Exception as e:
            raise ErrorConexionSQL(
                "No fue posible consultar el historial "
                f"de ejecuciones: {e}"
            ) from e