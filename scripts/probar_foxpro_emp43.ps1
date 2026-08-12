# IMPORTANTE: VFPOLEDB normalmente solo existe registrado en su versión de
# 32 bits. Si este script se ejecuta con el PowerShell de 64 bits por
# defecto, OleDbConnection.Open() puede fallar con un error de "proveedor
# no registrado" aunque el driver esté instalado. Ejecutar con:
#   %SystemRoot%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -File probar_foxpro_emp43.ps1

$ErrorActionPreference = 'Stop'

if (:Is64BitProcess) {
throw @'
Este script debe ejecutarse con PowerShell de 32 bits:

%SystemRoot%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe

Ejemplo:
C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -File .\scripts\probar_foxpro_emp43.ps1
'@
}

$dbc = 'C:\VSAI\Empresas\EMP43\sai.DBC'

if (-not (Test-Path -LiteralPath $dbc -PathType Leaf)) {
throw "No existe el archivo DBC: $dbc"
}

# se usa "Exclusive=No;BackgroundFetch=No;" (misma cadena que
# se validó como exitosa en las pruebas de conectividad) propiedad reconocida por VFPOLEDB.
$connectionString = @(
'Provider=VFPOLEDB.1'
"Data Source=$dbc"
'Collating Sequence=Machine'
'Exclusive=No'
'BackgroundFetch=No'
'Null=Yes'
'Deleted=Yes'
) -join ';'

$conn = New-Object System.Data.OleDb.OleDbConnection(
"$connectionString;"
)

$cmd = $null
$reader = $null

try {
    $conn.Open()
    $cmd = $conn.CreateCommand()
    $cmd.CommandTimeout = 15
    $cmd.CommandText = 'SELECT TOP 5 no_ped, cve_suc, lugar, cve_age, f_alta_ped FROM pedidoc ORDER BY no_ped, cve_suc'
    $reader = $cmd.ExecuteReader()
    $table = New-Object System.Data.DataTable
    $table.Load($reader)
    $table | Format-Table -AutoSize
    Write-Host "Conexión FoxPro EMP43 exitosa. Filas de prueba: $($table.Rows.Count)"
}
catch {
    throw
}
finally {
    if ($null -ne $reader) {
        $reader.Dispose()
    }
    
    if ($null -ne $cmd) {
        $cmd.Dispose()
    }
    
    if ($conn.State -ne 'Closed') {
        $conn.Close()
    }
    
    $conn.Dispose()
}
