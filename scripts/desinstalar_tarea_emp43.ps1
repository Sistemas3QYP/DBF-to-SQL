$ErrorActionPreference = 'Stop'
Unregister-ScheduledTask -TaskName 'Integracion SAI EMP43' -Confirm:$false
Write-Host 'Tarea eliminada.'
