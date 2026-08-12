/*
    IMPORTANTE:
    Cambiar el valor de @CuentaServicio antes de ejecutar.
*/

USE master;
GO

DECLARE @CuentaServicio sysname =
    N'QYPN\CuentaServicio';

IF @CuentaServicio = N'QYPN\CuentaServicio'
BEGIN
    THROW 50010,
        'Debe reemplazar QYPN\CuentaServicio por la cuenta real.',
        1;
END;

IF NOT EXISTS
(
    SELECT 1
    FROM sys.server_principals
    WHERE name = @CuentaServicio
)
BEGIN
    DECLARE @SqlLogin nvarchar(max);

    SET @SqlLogin =
        N'CREATE LOGIN '
        + QUOTENAME(@CuentaServicio)
        + N' FROM WINDOWS;';

    EXEC sys.sp_executesql @SqlLogin;
END;
GO

USE IntegracionSAIEmp43;
GO

DECLARE @CuentaServicio sysname =
    N'QYPN\CuentaServicio';

IF @CuentaServicio = N'QYPN\CuentaServicio'
BEGIN
    THROW 50011,
        'Debe reemplazar QYPN\CuentaServicio por la cuenta real.',
        1;
END;

IF NOT EXISTS
(
    SELECT 1
    FROM sys.database_principals
    WHERE name = @CuentaServicio
)
BEGIN
    DECLARE @SqlUsuario nvarchar(max);

    SET @SqlUsuario =
        N'CREATE USER '
        + QUOTENAME(@CuentaServicio)
        + N' FOR LOGIN '
        + QUOTENAME(@CuentaServicio)
        + N';';

    EXEC sys.sp_executesql @SqlUsuario;
END;

DECLARE @SqlPermisos nvarchar(max);

SET @SqlPermisos =
    N'GRANT SELECT, INSERT, UPDATE '
    + N'ON integracion.PedidoSAI TO '
    + QUOTENAME(@CuentaServicio)
    + N';'
    + N'GRANT SELECT, INSERT, DELETE '
    + N'ON integracion.PedidoSAI_Staging TO '
    + QUOTENAME(@CuentaServicio)
    + N';'
    + N'GRANT SELECT, INSERT, UPDATE '
    + N'ON integracion.BitacoraEjecucion TO '
    + QUOTENAME(@CuentaServicio)
    + N';'
    + N'GRANT EXECUTE '
    + N'ON integracion.SyncPedidosSAI TO '
    + QUOTENAME(@CuentaServicio)
    + N';';

EXEC sys.sp_executesql @SqlPermisos;
GO