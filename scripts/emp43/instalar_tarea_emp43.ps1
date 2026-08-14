# Ejecutar como Administrador
$ErrorActionPreference = 'Stop'

$name   = 'Integracion SAI EMP43'
$cmd    = 'C:\Integraciones\scripts\ejecutar_emp43.cmd'
$user   = 'qypn\sistemas03'
$cmdExe = "$env:SystemRoot\System32\cmd.exe"

if ($user -eq 'QYPN\CuentaServicio') {
    throw 'Debe reemplazar QYPN\CuentaServicio por la cuenta real.'
}

if (-not (Test-Path -LiteralPath $cmd -PathType Leaf)) {
    throw "No existe el archivo de ejecución: $cmd"
}

$action = New-ScheduledTaskAction `
    -Execute $cmdExe `
    -Argument "/d /c `"$cmd`"" `
    -WorkingDirectory 'C:\Integraciones'

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 2) `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

$password = Read-Host "Contraseña de $user" -AsSecureString
$cred = New-Object System.Management.Automation.PSCredential($user, $password)

Register-ScheduledTask `
    -TaskName $name `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description 'Sincroniza pedidos EMP43 cada 5 minutos (FoxPro a SQL Server)' `
    -User $user `
    -Password $cred.GetNetworkCredential().Password `
    -RunLevel Highest `
    -Force

Write-Host "Tarea '$name' registrada correctamente."
