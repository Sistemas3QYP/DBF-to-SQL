USE IntegracionSAIEmp64;
GO

CREATE OR ALTER PROCEDURE integracion.SyncPedidosSAI
    @IdEjecucion uniqueidentifier
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @Insertados int = 0;
    DECLARE @Actualizados int = 0;
    DECLARE @ObservadosSinCambios int = 0;

    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS
        (
            SELECT 1
            FROM integracion.PedidoSAI_Staging
            WHERE IdEjecucion = @IdEjecucion
        )
        BEGIN
            THROW 50001,
                'No existen registros de staging para la ejecución indicada.',
                1;
        END;

        /* 1. Actualizar pedidos modificados */
        UPDATE destino
        SET
            Lugar = origen.Lugar,
            HoraPedido = origen.HoraPedido,
            Estatus = origen.Estatus,
            Estatus2 = origen.Estatus2,
            FechaAltaPedido = origen.FechaAltaPedido,
            ClaveAgente = origen.ClaveAgente,
            ClaveCliente = origen.ClaveCliente,
            HashOrigen = origen.HashOrigen
        FROM integracion.PedidoSAI AS destino
        INNER JOIN integracion.PedidoSAI_Staging AS origen
            ON origen.NoPedido = destino.NoPedido
           AND origen.ClaveSucursal = destino.ClaveSucursal
           AND origen.IdEjecucion = @IdEjecucion
        WHERE destino.HashOrigen <> origen.HashOrigen;

        SET @Actualizados = @@ROWCOUNT;

        /* 2. Contar pedidos observados sin cambios */
        SELECT
            @ObservadosSinCambios = COUNT(*)
        FROM integracion.PedidoSAI AS destino
        INNER JOIN integracion.PedidoSAI_Staging AS origen
            ON origen.NoPedido = destino.NoPedido
           AND origen.ClaveSucursal = destino.ClaveSucursal
           AND origen.IdEjecucion = @IdEjecucion
        WHERE destino.HashOrigen = origen.HashOrigen;

        /* 3. Insertar pedidos nuevos */
        INSERT INTO integracion.PedidoSAI
        (
            NoPedido,
            ClaveSucursal,
            Lugar,
            HoraPedido,
            Estatus,
            Estatus2,
            FechaAltaPedido,
            ClaveAgente,
            ClaveCliente,
            HashOrigen
        )
        SELECT
            origen.NoPedido,
            origen.ClaveSucursal,
            origen.Lugar,
            origen.HoraPedido,
            origen.Estatus,
            origen.Estatus2,
            origen.FechaAltaPedido,
            origen.ClaveAgente,
            origen.ClaveCliente,
            origen.HashOrigen
        FROM integracion.PedidoSAI_Staging AS origen
        WHERE origen.IdEjecucion = @IdEjecucion
          AND NOT EXISTS
          (
              SELECT 1
              FROM integracion.PedidoSAI AS destino
                   WITH (UPDLOCK, HOLDLOCK)
              WHERE destino.NoPedido = origen.NoPedido
                AND destino.ClaveSucursal = origen.ClaveSucursal
          );

        SET @Insertados = @@ROWCOUNT;

        /* 4. Limpiar staging del lote actual */
        DELETE FROM integracion.PedidoSAI_Staging
        WHERE IdEjecucion = @IdEjecucion;

        COMMIT TRANSACTION;

        SELECT
            @Insertados
                AS RegistrosInsertados,
            @Actualizados
                AS RegistrosActualizados,
            @ObservadosSinCambios
                AS RegistrosObservadosSinCambios;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
        BEGIN
            ROLLBACK TRANSACTION;
        END;

        THROW;
    END CATCH;
END;
GO