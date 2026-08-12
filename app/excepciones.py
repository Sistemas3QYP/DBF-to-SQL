from __future__ import annotations
"""Excepciones controladas del proyecto de integración."""

class ErrorIntegracion(Exception): 
    """Base de todas las excepciones de la integración."""

class ErrorConfiguracion(ErrorIntegracion): 
    """La configuración es inválida, incompleta o insegura."""

class ErrorConexionFoxPro(ErrorIntegracion): 
    """No fue posible conectar con Visual FoxPro / VFPOLEDB."""
    
class ErrorConsultaFoxPro(ErrorIntegracion): 
    """Error al ejecutar la consulta de extracción sobre FoxPro."""

class ErrorConexionSQL(ErrorIntegracion): 
    """No fue posible conectar con SQL Server."""

class ErrorCargaStaging(ErrorIntegracion): 
    """No fue posible cargar el lote en staging."""

class ErrorSincronizacionSQL(ErrorIntegracion): 
    """El procedimiento de sincronización SQL falló."""

class ErrorValidacionDatos(ErrorIntegracion): 
    """Los datos extraídos no son válidos o que no cumplen las reglas de validación."""

class EjecucionEnCurso(ErrorIntegracion): 
    """Ya existe una ejecución activa para la misma empresa."""