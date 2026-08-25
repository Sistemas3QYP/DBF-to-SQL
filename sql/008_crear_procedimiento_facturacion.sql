USE IntegracionSAIEmp64;
GO

CREATE OR ALTER PROCEDURE
    integracion.SyncFacturasPedidoSAI
    @IdEjecucion uniqueidentifier
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @Actualizados int = 0;
    DECLARE @SinCambios int = 0;
    DECLARE @NoEncontrados int = 0;

    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS
        (
            SELECT 1
            FROM integracion.FacturaPedidoSAI_Staging
            WHERE IdEjecucion = @IdEjecucion
        )
        BEGIN
            THROW 50002,
                'No existen registros de facturación en staging.',
                1;
        END;

        /* Facturas cuyo pedido no existe en PedidoSAI */
        SELECT
            @NoEncontrados = COUNT(*)
        FROM integracion.FacturaPedidoSAI_Staging AS origen
        WHERE origen.IdEjecucion = @IdEjecucion
          AND NOT EXISTS
          (
              SELECT 1
              FROM integracion.PedidoSAI AS destino
              WHERE destino.NoPedido = origen.NoPedido
                AND destino.ClaveSucursal = origen.ClaveSucursal
          );

        /* Facturas que no cambiaron */
        SELECT
            @SinCambios = COUNT(*)
        FROM integracion.PedidoSAI AS destino
        INNER JOIN integracion.FacturaPedidoSAI_Staging AS origen
            ON origen.NoPedido = destino.NoPedido
           AND origen.ClaveSucursal = destino.ClaveSucursal
           AND origen.IdEjecucion = @IdEjecucion
        WHERE ISNULL(destino.NoFactura, '') =
              origen.NoFactura
          AND destino.FechaFactura =
              origen.FechaFactura
          AND
          (
              destino.HoraFactura =
                  origen.HoraFactura
              OR
              (
                  destino.HoraFactura IS NULL
                  AND origen.HoraFactura IS NULL
              )
          );

        /* Actualizar facturas que cambiaron */
        UPDATE destino
        SET
            NoFactura = origen.NoFactura,
            FechaFactura = origen.FechaFactura,
            HoraFactura = origen.HoraFactura
        FROM integracion.PedidoSAI AS destino
        INNER JOIN integracion.FacturaPedidoSAI_Staging AS origen
            ON origen.NoPedido = destino.NoPedido
           AND origen.ClaveSucursal = destino.ClaveSucursal
           AND origen.IdEjecucion = @IdEjecucion
        WHERE
            ISNULL(destino.NoFactura, '') <>
                origen.NoFactura
            OR destino.FechaFactura IS NULL
            OR destino.FechaFactura <>
                origen.FechaFactura
            OR
            (
                destino.HoraFactura <>
                    origen.HoraFactura
                OR
                (
                    destino.HoraFactura IS NULL
                    AND origen.HoraFactura IS NOT NULL
                )
                OR
                (
                    destino.HoraFactura IS NOT NULL
                    AND origen.HoraFactura IS NULL
                )
            );

        SET @Actualizados = @@ROWCOUNT;

        DELETE
        FROM integracion.FacturaPedidoSAI_Staging
        WHERE IdEjecucion = @IdEjecucion;

        COMMIT TRANSACTION;

        SELECT
            @Actualizados
                AS RegistrosFacturasActualizados,
            @SinCambios
                AS RegistrosFacturasSinCambios,
            @NoEncontrados
                AS RegistrosFacturasSinPedido;
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