USE IntegracionSAIEmp64;
GO

SET XACT_ABORT ON;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    /* ============================================================
       1. Eliminar constraints default de columnas operativas
       ============================================================ */

    IF OBJECT_ID(
        N'integracion.DF_PedidoSAI_FechaPrimeraImportacion',
        N'D'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        DROP CONSTRAINT
            DF_PedidoSAI_FechaPrimeraImportacion;
    END;

    IF OBJECT_ID(
        N'integracion.DF_PedidoSAI_FechaUltimaModificacion',
        N'D'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        DROP CONSTRAINT
            DF_PedidoSAI_FechaUltimaModificacion;
    END;

    IF OBJECT_ID(
        N'integracion.DF_PedidoSAI_FechaUltimaObservacion',
        N'D'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        DROP CONSTRAINT
            DF_PedidoSAI_FechaUltimaObservacion;
    END;

    /* ============================================================
       2. Eliminar columnas no utilizadas de PedidoSAI
       ============================================================ */

    IF COL_LENGTH(
        N'integracion.PedidoSAI',
        N'FechaEntrega'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        DROP COLUMN FechaEntrega;
    END;

    IF COL_LENGTH(
        N'integracion.PedidoSAI',
        N'SubtotalPedido'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        DROP COLUMN SubtotalPedido;
    END;

    IF COL_LENGTH(
        N'integracion.PedidoSAI',
        N'ClaveVendedor4'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        DROP COLUMN ClaveVendedor4;
    END;

    IF COL_LENGTH(
        N'integracion.PedidoSAI',
        N'ClaveVendedor5'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        DROP COLUMN ClaveVendedor5;
    END;

    IF COL_LENGTH(
        N'integracion.PedidoSAI',
        N'FechaPrimeraImportacion'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        DROP COLUMN FechaPrimeraImportacion;
    END;

    IF COL_LENGTH(
        N'integracion.PedidoSAI',
        N'FechaUltimaModificacion'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        DROP COLUMN FechaUltimaModificacion;
    END;

    IF COL_LENGTH(
        N'integracion.PedidoSAI',
        N'FechaUltimaObservacion'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI
        DROP COLUMN FechaUltimaObservacion;
    END;

    /* ============================================================
       3. Eliminar columnas no utilizadas de staging
       ============================================================ */

    IF COL_LENGTH(
        N'integracion.PedidoSAI_Staging',
        N'FechaEntrega'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI_Staging
        DROP COLUMN FechaEntrega;
    END;

    IF COL_LENGTH(
        N'integracion.PedidoSAI_Staging',
        N'SubtotalPedido'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI_Staging
        DROP COLUMN SubtotalPedido;
    END;

    IF COL_LENGTH(
        N'integracion.PedidoSAI_Staging',
        N'ClaveVendedor4'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI_Staging
        DROP COLUMN ClaveVendedor4;
    END;

    IF COL_LENGTH(
        N'integracion.PedidoSAI_Staging',
        N'ClaveVendedor5'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE integracion.PedidoSAI_Staging
        DROP COLUMN ClaveVendedor5;
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