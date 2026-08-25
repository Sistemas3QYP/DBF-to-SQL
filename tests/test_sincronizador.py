import logging
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from app.excepciones import ErrorConexionSQL
from app.modelos import ConfiguracionAplicacion
from app.sincronizador import Sincronizador

def _cfg() -> ConfiguracionAplicacion:
    return ConfiguracionAplicacion(
        ambiente="PRODUCCION",
        empresa="EMP64",
        dbc=Path("C:/VSAI/Empresas/EMP64/sai.DBC"),
        provider="VFPOLEDB.1",
        collating_sequence="Machine",
        sql_servidor="SRVERPQYPN\\SQLEXPRESS",
        sql_base_datos="IntegracionSAIEmp64",
        sql_driver="ODBC Driver 18 for SQL Server",
        autenticacion_windows=True,
        encrypt=True,
        trust_server_certificate=True,
        lugar="GENERAL",
        agentes=(3101, 3102, 3103, 3104),
        fecha_inicial=date(2026, 8, 1),
        ventana_dias=4,
        reintentos_maximos=1,
        espera_segundos=0,
        tamano_lote=250,
        lock_max_minutos=60,
        retencion_staging_dias=7,
    )

class FoxProFalso:
    def __init__(self, filas, filas_facturas=None):
        self.filas = filas
        self.filas_facturas = filas_facturas or []

    def extraer(self, fecha_desde):
        return self.filas

    def extraer_facturas(self, fecha_desde):
        return self.filas_facturas

    @staticmethod
    def es_transitorio(exc):
        return False


class SqlFalso:
    def __init__(self, ya_completada: bool):
        self.ya_completada = ya_completada
        self.staging_cargado = None
        self.finalizado = None

    def hay_ejecucion_completada(self):
        return self.ya_completada

    def iniciar(self, id_ejecucion, fecha_desde, tipo):
        self.tipo_iniciado = tipo

    def finalizar(self, id_ejecucion, estado, extraidos=0, insertados=0, actualizados=0, intentos=1, error=None):
        self.finalizado = estado

    def cargar_staging(self, id_ejecucion, pedidos):
        self.staging_cargado = pedidos

    def sincronizar(self, id_ejecucion):
        if self.staging_cargado is None:
            return 0, 0, 0
        return len(self.staging_cargado), 0, 0
    
    def cargar_staging_facturas(self, id_ejecucion, facturas):
        self.facturas_staging = facturas

    def sincronizar_facturas(self, id_ejecucion):
        return 0, 0, 0

def _logger():
    logger = logging.getLogger("test_sincronizador")
    logger.addHandler(logging.NullHandler())
    return logger

def _fila_valida():
    return (
        Decimal(10025),
        "001",
        "GENERAL",
        "1159",
        "ABIERTO",
        "SURTIDO",
        "2026-08-10",
        Decimal(3101),
        Decimal(500),
    )

def test_primera_ejecucion_es_inicial():
    sql = SqlFalso(ya_completada=False)
    fox = FoxProFalso([_fila_valida()])
    sinc = Sincronizador(_cfg(), fox, sql, _logger())
    resultado = sinc.ejecutar(uuid4())
    assert sql.tipo_iniciado == "INICIAL"
    assert resultado.estado == "COMPLETADA"
    assert resultado.insertados == 1

def test_ejecucion_posterior_es_incremental():
    sql = SqlFalso(ya_completada=True)
    fox = FoxProFalso([_fila_valida()])
    sinc = Sincronizador(_cfg(), fox, sql, _logger())
    sinc.ejecutar(uuid4())
    assert sql.tipo_iniciado == "INCREMENTAL"

def test_sin_registros_no_llama_sincronizar():
    sql = SqlFalso(ya_completada=True)
    fox = FoxProFalso([])
    sinc = Sincronizador(_cfg(), fox, sql, _logger())
    resultado = sinc.ejecutar(uuid4())
    assert resultado.estado == "SIN_REGISTROS"
    assert sql.staging_cargado is None

def test_error_conexion_sql_al_verificar_historial_se_propaga():
    class SqlQueFalla(SqlFalso):
        def hay_ejecucion_completada(self):
            raise ErrorConexionSQL("SQL Server no disponible")

    sql = SqlQueFalla(ya_completada=False)
    fox = FoxProFalso([_fila_valida()])
    sinc = Sincronizador(_cfg(), fox, sql, _logger())

    try:
        sinc.ejecutar(uuid4())
        assert False, "Se esperaba ErrorConexionSQL"
    except ErrorConexionSQL:
        pass

def test_pedidos_llevan_hash_de_32_bytes():
    sql = SqlFalso(ya_completada=False)
    fox = FoxProFalso([_fila_valida()])

    sinc = Sincronizador(
        _cfg(),
        fox,
        sql,
        _logger(),
    )

    sinc.ejecutar(uuid4())

    assert sql.staging_cargado is not None
    assert len(sql.staging_cargado) == 1
    assert len(
        sql.staging_cargado[0].hash_origen
    ) == 32