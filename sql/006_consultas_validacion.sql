USE IntegracionSAIEmp43;
GO

-- Últimas ejecuciones
SELECT TOP (50)
    IdEjecucion,
    FechaInicio,
    FechaFin,
    FechaDesdeFoxPro,
    TipoEjecucion,
    Estado,
    RegistrosExtraidos,
    RegistrosInsertados,
    RegistrosActualizados,
    NumeroIntentos,
    MensajeError
FROM integracion.BitacoraEjecucion
ORDER BY FechaInicio DESC;
GO

-- Totales en tabla productiva
SELECT COUNT(*) AS TotalPedidos
FROM integracion.PedidoSAI;
GO

-- Últimos pedidos observados
SELECT TOP (50) *
FROM integracion.PedidoSAI
ORDER BY FechaUltimaObservacion DESC;
GO

-- Residuos en staging (debería estar vacío tras ejecuciones correctas)
SELECT IdEjecucion, COUNT(*) AS Registros
FROM integracion.PedidoSAI_Staging
GROUP BY IdEjecucion;
GO
