USE IntegracionSAIEmp43;
GO

IF SCHEMA_ID(N'integracion') IS NULL
BEGIN
    EXEC('CREATE SCHEMA integracion');
END;
GO

/* Tabla productiva */
IF OBJECT_ID(N'integracion.PedidoSAI', N'U') IS NULL
BEGIN
    CREATE TABLE integracion.PedidoSAI
    (
        NoPedido                  decimal(10,0)   NOT NULL,
        ClaveSucursal             varchar(3)      NOT NULL,
        Lugar                     varchar(10)     NOT NULL,
        HoraPedido                time(0)         NULL,
        Estatus                   varchar(15)     NOT NULL,
        Estatus2                  varchar(15)     NOT NULL,
        FechaAltaPedido           date            NOT NULL,
        FechaEntrega              date            NULL,
        ClaveAgente               decimal(5,0)    NOT NULL,
        ClaveCliente              decimal(5,0)    NOT NULL,
        SubtotalPedido            decimal(19,6)   NOT NULL,
        ClaveVendedor4            decimal(5,0)    NOT NULL,
        ClaveVendedor5            decimal(5,0)    NOT NULL,
        HashOrigen                binary(32)      NOT NULL,
        FechaPrimeraImportacion   datetime2(0)    NOT NULL
            CONSTRAINT DF_PedidoSAI_FechaPrimeraImportacion DEFAULT (SYSDATETIME()),
        FechaUltimaModificacion   datetime2(0)    NOT NULL
            CONSTRAINT DF_PedidoSAI_FechaUltimaModificacion DEFAULT (SYSDATETIME()),
        FechaUltimaObservacion    datetime2(0)    NOT NULL
            CONSTRAINT DF_PedidoSAI_FechaUltimaObservacion DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_PedidoSAI PRIMARY KEY (NoPedido, ClaveSucursal)
    );
END;
GO

/* Staging por ejecución */
IF OBJECT_ID(N'integracion.PedidoSAI_Staging', N'U') IS NULL
BEGIN
    CREATE TABLE integracion.PedidoSAI_Staging
    (
        IdEjecucion     uniqueidentifier NOT NULL,
        NoPedido        decimal(10,0)    NOT NULL,
        ClaveSucursal   varchar(3)       NOT NULL,
        Lugar           varchar(10)      NOT NULL,
        HoraPedido      time(0)          NULL,
        Estatus         varchar(15)      NOT NULL,
        Estatus2        varchar(15)      NOT NULL,
        FechaAltaPedido date             NOT NULL,
        FechaEntrega    date             NULL,
        ClaveAgente     decimal(5,0)     NOT NULL,
        ClaveCliente    decimal(5,0)     NOT NULL,
        SubtotalPedido  decimal(19,6)    NOT NULL,
        ClaveVendedor4  decimal(5,0)     NOT NULL,
        ClaveVendedor5  decimal(5,0)     NOT NULL,
        HashOrigen      binary(32)       NOT NULL,
        CONSTRAINT PK_PedidoSAI_Staging PRIMARY KEY (IdEjecucion, NoPedido, ClaveSucursal)
    );
END;
GO

/* Bitácora de ejecuciones */
IF OBJECT_ID(N'integracion.BitacoraEjecucion', N'U') IS NULL
BEGIN
    CREATE TABLE integracion.BitacoraEjecucion
    (
        IdEjecucion             uniqueidentifier NOT NULL,
        FechaInicio             datetime2(0)     NOT NULL,
        FechaFin                datetime2(0)     NULL,
        FechaDesdeFoxPro        date             NOT NULL,
        TipoEjecucion           varchar(20)      NOT NULL,
        Estado                  varchar(20)      NOT NULL,
        RegistrosExtraidos      int              NULL,
        RegistrosInsertados     int              NULL,
        RegistrosActualizados   int              NULL,
        NumeroIntentos          int              NOT NULL
            CONSTRAINT DF_Bitacora_NumeroIntentos DEFAULT (1),
        MensajeError            nvarchar(4000)   NULL,
        CONSTRAINT PK_BitacoraEjecucion PRIMARY KEY (IdEjecucion)
    );
END;
GO
