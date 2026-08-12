@echo off
setlocal

set "BASE=C:\Integraciones\SAI"
set "PYTHON=%BASE%\.venv\Scripts\python.exe"
set "CONFIG=%BASE%\config\emp43.json"

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