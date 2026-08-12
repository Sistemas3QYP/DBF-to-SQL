USE IntegracionSAIEmp43;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_PedidoSAI_Staging_Pedido'
      AND object_id = OBJECT_ID(N'integracion.PedidoSAI_Staging')
)
BEGIN
    CREATE INDEX IX_PedidoSAI_Staging_Pedido
        ON integracion.PedidoSAI_Staging (NoPedido, ClaveSucursal, IdEjecucion);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_Bitacora_Estado_Fecha'
      AND object_id = OBJECT_ID(N'integracion.BitacoraEjecucion')
)
BEGIN
    CREATE INDEX IX_Bitacora_Estado_Fecha
        ON integracion.BitacoraEjecucion (Estado, FechaInicio);
END;
GO
