# Integración SAI EMP43 / EMP64

Sincronización de solo lectura desde Visual FoxPro (DBF/DBC) hacia SQL Server Express.

## Objetivo

- Eliminar la dependencia de Excel.
- Extraer periódicamente pedidos de `pedidoc` (solo lectura).
- Detectar altas y modificaciones mediante hash SHA-256.
- Cargar en SQL Server (`PedidoSAI`) sin eliminar registros que dejen de cumplir filtros.
- Ejecutarse cada 5 minutos mediante Task Scheduler + Python 32-bit.

## Requisitos

- Windows y Python x86 de 32 bits.
- VFPOLEDB de 32 bits.
- ODBC Driver 18 for SQL Server.
- Acceso de lectura a `C:\VSAI\Empresas\EMP43` (o EMP64).
- Autenticación integrada de Windows en SQL Server.

## Estructura

```
C:\Integraciones\SAI\
├── app\                  # Código Python
├── config\               # emp43.json / emp64.json
├── sql\                  # Scripts de creación
├── scripts\              # .cmd y .ps1 de operación
├── tests\
├── logs\                 # Generados en runtime
├── runtime\              # Archivos .lock
├── .venv\
├── requirements.txt
└── README.md
```

## Instalación

1. Copiar el proyecto a `C:\Integraciones\SAI`.
2. Crear entorno virtual 32-bit:
   ```bat
   py -3.12-32 -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. Ejecutar scripts SQL en orden (`001` → `005`). Ajustar `005_crear_permisos.sql` con la cuenta de servicio.
4. Probar conectividad (ver advertencia de bitness abajo):
   ```powershell
   .\scripts\probar_foxpro_emp43.ps1
   .\scripts\probar_sql_emp43.ps1
   ```
5. Ejecutar pruebas unitarias:
   ```bat
   .venv\Scripts\python.exe -m pytest tests -q
   ```
6. Ejecución manual:
   ```bat
   scripts\ejecutar_emp43.cmd
   ```
7. Instalar la tarea programada (como Administrador):
   ```powershell
   .\scripts\instalar_tarea_emp43.ps1
   ```
## Códigos de salida

| Código | Significado              |
|--------|--------------------------|
| 0      | Ejecución correcta       |
| 1      | Error general            |
| 2      | Configuración inválida   |
| 3      | FoxPro no disponible     |
| 4      | SQL Server no disponible |
| 5      | Validación de datos      |
| 6      | Ejecución duplicada      |
| 7      | Error de sincronización SQL |

## Reglas de negocio implementadas

- Solo `lugar = 'GENERAL'`
- Solo agentes `3101, 3102, 3103, 3104`
- Fecha inicial: `2026-08-01`
- Ventana móvil de 4 días (modificable + 1 día de margen)
- No se eliminan pedidos de la tabla final aunque dejen de cumplir filtros
- Hash SHA-256 sobre campos normalizados para detectar cambios

## Advertencias antes de producción

1. Confirmar tipos reales de `hora_ped`, `status`, `status2` y campos numéricos en la empresa destino.
2. Validar que VFPOLEDB acepte parámetros (`?`) en la consulta; no concatenar valores.
3. Sustituir la cuenta de servicio en los scripts de permisos y de Task Scheduler.
4. Probar primero en ambiente de pruebas y respaldar SQL antes de la carga inicial.
5. La primera ejecución exitosa marca el paso de tipo `INICIAL` a `INCREMENTAL`.
6. **VFPOLEDB casi siempre está registrado solo en 32 bits.** Los scripts
   `.ps1` que usan `System.Data.OleDb.OleDbConnection` deben ejecutarse con
   el PowerShell de 32 bits
   (`%SystemRoot%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe`), o
   fallarán con un error de "proveedor no registrado" aunque el driver esté
   instalado correctamente.
7. El identificador de provider usado en `config/*.json` es `VFPOLEDB.1`
   (con el `.1` de versión de ProgID de COM). Si el servidor tiene
   registrada otra versión, ajustar el valor de `foxpro.provider` — es
   configurable justo para no tener que tocar código.
8. Este proyecto **solo soporta autenticación de Windows** hacia SQL
   Server (`autenticacion_windows: true`); no hay implementación de
   usuario/contraseña. La validación de configuración lo exige
   explícitamente.

## .gitignore relevante

Los archivos `logs/*.log` y `runtime/*.lock` se generan en tiempo de
ejecución y no deben versionarse (ver `.gitignore`).