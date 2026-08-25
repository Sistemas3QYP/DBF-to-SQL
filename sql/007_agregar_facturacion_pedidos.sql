USE IntegracionSAIEmp64;
GO

SET XACT_ABORT ON;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    /* ============================================================
       1. Agregar columnas de facturación a la tabla productiva
       ============================================================ */

    IF COL_LENGTH(
        N'integracion.PedidoSAI',
        N'NoFactura'
    ) IS NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        ADD NoFactura varchar(10) NULL;
    END;

    IF COL_LENGTH(
        N'integracion.PedidoSAI',
        N'FechaFactura'
    ) IS NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        ADD FechaFactura date NULL;
    END;

    IF COL_LENGTH(
        N'integracion.PedidoSAI',
        N'HoraFactura'
    ) IS NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        ADD HoraFactura time(0) NULL;
    END;

    /* ============================================================
       2. Crear staging exclusivo para facturación
       ============================================================ */

    IF OBJECT_ID(
        N'integracion.FacturaPedidoSAI_Staging',
        N'U'
    ) IS NULL
    BEGIN
        CREATE TABLE integracion.FacturaPedidoSAI_Staging
        (
            IdEjecucion    uniqueidentifier NOT NULL,
            NoPedido       decimal(10,0)    NOT NULL,
            ClaveSucursal  varchar(3)       NOT NULL,
            NoFactura      varchar(10)      NOT NULL,
            FechaFactura   date             NOT NULL,
            HoraFactura    time(0)          NULL,

            CONSTRAINT PK_FacturaPedidoSAI_Staging
                PRIMARY KEY
                (
                    IdEjecucion,
                    NoPedido,
                    ClaveSucursal
                )
        );
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
    BEGIN
        ROLLBACK TRANSACTION;
    END;

    THROW;
END CATCH;
GO

/* ================================================================
   3. Índice auxiliar para localizar pedidos
   ================================================================ */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_FacturaPedidoSAI_Staging_Pedido'
      AND object_id =
          OBJECT_ID(N'integracion.FacturaPedidoSAI_Staging')
)
BEGIN
    CREATE INDEX IX_FacturaPedidoSAI_Staging_Pedido
        ON integracion.FacturaPedidoSAI_Staging
        (
            NoPedido,
            ClaveSucursal,
            IdEjecucion
        );
END;
GO