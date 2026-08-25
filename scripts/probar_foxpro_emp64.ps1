# IMPORTANTE: VFPOLEDB normalmente solo existe registrado en su versión de
# 32 bits. Si este script se ejecuta con el PowerShell de 64 bits por
# defecto, OleDbConnection.Open() puede fallar con un error de "proveedor
# no registrado" aunque el driver esté instalado. Ejecutar con:
#   %SystemRoot%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -File probar_foxpro_emp64.ps1

$ErrorActionPreference = 'Stop'

if ([Environment]::Is64BitProcess) {
    throw @'
Este script debe ejecutarse con PowerShell de 32 bits:

%SystemRoot%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe

Ejemplo:
C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -File .\scripts\probar_foxpro_emp64.ps1
'@
}

$dbc = 'C:\VSAI\Empresas\EMP64\sai.DBC'

if (-not (Test-Path -LiteralPath $dbc -PathType Leaf)) {
    throw "No existe el archivo DBC: $dbc"
}

$connectionString = @(
'Provider=VFPOLEDB.1'
"Data Source=C:\VSAI\Empresas\EMP64\sai.DBC"
'Exclusive=No'
) -join ';'

$conn = New-Object System.Data.OleDb.OleDbConnection("$connectionString;")

$cmd = $null
$reader = $null

try {
    $conn.Open()
    $cmd = $conn.CreateCommand()
    $cmd.CommandTimeout = 15
    $cmd.CommandText = 'SELECT COUNT(*) AS Total FROM pedidoc WHERE lugar = "GENERAL" AND cve_age IN (3101,3102,3103,3104) AND f_alta_ped >= {^2026-08-01}'
    $reader = $cmd.ExecuteReader()
    $table = New-Object System.Data.DataTable
    $table.Load($reader)
    $table | Format-Table -AutoSize
    Write-Host "Conexión FoxPro EMP64 exitosa. Filas de prueba: $($table.Rows.Count)"
}
finally {
    if ($null -ne $reader) { $reader.Dispose() }
    if ($null -ne $cmd) { $cmd.Dispose() }
    if ($conn.State -ne 'Closed') { $conn.Close() }
    $conn.Dispose()
}
