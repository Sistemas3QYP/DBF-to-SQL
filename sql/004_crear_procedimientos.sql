USE IntegracionSAIEmp43;
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
    DECLARE @Ahora datetime2(0) = SYSDATETIME();

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
        UPDATE d
        SET
            Lugar = s.Lugar,
            HoraPedido = s.HoraPedido,
            Estatus = s.Estatus,
            Estatus2 = s.Estatus2,
            FechaAltaPedido = s.FechaAltaPedido,
            FechaEntrega = s.FechaEntrega,
            ClaveAgente = s.ClaveAgente,
            ClaveCliente = s.ClaveCliente,
            SubtotalPedido = s.SubtotalPedido,
            ClaveVendedor4 = s.ClaveVendedor4,
            ClaveVendedor5 = s.ClaveVendedor5,
            HashOrigen = s.HashOrigen,
            FechaUltimaModificacion = @Ahora,
            FechaUltimaObservacion = @Ahora
        FROM integracion.PedidoSAI AS d
        INNER JOIN integracion.PedidoSAI_Staging AS s
            ON s.NoPedido = d.NoPedido
           AND s.ClaveSucursal = d.ClaveSucursal
           AND s.IdEjecucion = @IdEjecucion
        WHERE d.HashOrigen <> s.HashOrigen;

        SET @Actualizados = @@ROWCOUNT;

        /* 2. Actualizar solo observación de pedidos sin cambios */
        UPDATE d
        SET
            FechaUltimaObservacion = @Ahora
        FROM integracion.PedidoSAI AS d
        INNER JOIN integracion.PedidoSAI_Staging AS s
            ON s.NoPedido = d.NoPedido
           AND s.ClaveSucursal = d.ClaveSucursal
           AND s.IdEjecucion = @IdEjecucion
        WHERE d.HashOrigen = s.HashOrigen;

        SET @ObservadosSinCambios = @@ROWCOUNT;

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
            FechaEntrega,
            ClaveAgente,
            ClaveCliente,
            SubtotalPedido,
            ClaveVendedor4,
            ClaveVendedor5,
            HashOrigen,
            FechaPrimeraImportacion,
            FechaUltimaModificacion,
            FechaUltimaObservacion
        )
        SELECT
            s.NoPedido,
            s.ClaveSucursal,
            s.Lugar,
            s.HoraPedido,
            s.Estatus,
            s.Estatus2,
            s.FechaAltaPedido,
            s.FechaEntrega,
            s.ClaveAgente,
            s.ClaveCliente,
            s.SubtotalPedido,
            s.ClaveVendedor4,
            s.ClaveVendedor5,
            s.HashOrigen,
            @Ahora,
            @Ahora,
            @Ahora
        FROM integracion.PedidoSAI_Staging AS s
        WHERE s.IdEjecucion = @IdEjecucion
          AND NOT EXISTS
          (
              SELECT 1
              FROM integracion.PedidoSAI AS d
                   WITH (UPDLOCK, HOLDLOCK)
              WHERE d.NoPedido = s.NoPedido
                AND d.ClaveSucursal = s.ClaveSucursal
          );

        SET @Insertados = @@ROWCOUNT;

        DELETE FROM integracion.PedidoSAI_Staging
        WHERE IdEjecucion = @IdEjecucion;

        COMMIT TRANSACTION;

        SELECT
            @Insertados AS RegistrosInsertados,
            @Actualizados AS RegistrosActualizados,
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