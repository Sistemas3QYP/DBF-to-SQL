$ErrorActionPreference = 'Stop'
Unregister-ScheduledTask -TaskName 'Integracion SAI EMP64' -Confirm:$false
Write-Host 'Tarea eliminada.'
