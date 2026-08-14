@echo off
setlocal

set "BASE=C:\Integraciones"
set "PYTHON=%BASE%\.venv\Scripts\python.exe"
set "CONFIG=%BASE%\config\emp64.json"

if not exist "%PYTHON%" (
    echo No existe Python del entorno virtual: %PYTHON%
    exit /b 2
)

if not exist "%CONFIG%" (
    echo No existe la configuracion: %CONFIG%
    exit /b 2
)

cd /d "%BASE%"

"%PYTHON%" -m app.main --config "%CONFIG%"
set "CODIGO=%ERRORLEVEL%"

exit /b %CODIGO%