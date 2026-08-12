$ErrorActionPreference = 'Stop'
$cs = 'Server=SRVERPQYPN\SQLEXPRESS;Database=IntegracionSAIEmp43;Integrated Security=True;Encrypt=True;TrustServerCertificate=True'

$c = New-Object System.Data.SqlClient.SqlConnection($cs)
try {
    $c.Open()
    Write-Host 'Conexión SQL Server exitosa.'
}
finally {
    if ($c.State -eq 'Open') { $c.Close() }
    $c.Dispose()
}
