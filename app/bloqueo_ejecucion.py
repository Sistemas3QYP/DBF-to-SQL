from __future__ import annotations
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import psutil
from .excepciones import EjecucionEnCurso

"""
La regla es:
    - Si el PID existe, siempre se considera ejecución activa.
    - Si el PID no existe, el bloqueo es obsoleto.
    - Si el archivo está corrupto pero es reciente, no se elimina.
    - Si el archivo está corrupto y supera el tiempo máximo, se elimina.
    - Se guarda la fecha de creación del proceso para reducir el riesgo de reutilización de PID.
"""


class BloqueoEjecucion:
    """
    Context manager que garantiza una sola ejecución activa por empresa.
    - Crea un archivo .lock con PID y timestamp.
    - Detecta bloqueos obsoletos (proceso muerto o timeout).
    - Elimina el lock al salir (incluso con excepción).
    """

    def __init__(self, ruta: Path | str, max_minutos: int = 60):
        self.ruta = Path(ruta)
        self.max = timedelta(minutes=max_minutos)
        self.adquirido = False

    def __enter__(self) -> "BloqueoEjecucion":
        self.ruta.parent.mkdir(
        parents=True,
        exist_ok=True,
        )

        if self.ruta.exists():
            self._evaluar_bloqueo_existente()
    
        datos = {
            "pid": os.getpid(),
            "inicio": datetime.now().isoformat(
            timespec="seconds"
            ),
            "creacion_proceso": _creacion_proceso(os.getpid()),
        }

        try:
            with self.ruta.open(
                "x",
                encoding="utf-8",
            ) as archivo:
                json.dump(
                    datos,
                    archivo,
                    ensure_ascii=False,
                    indent=2,
                )
                archivo.flush()
                os.fsync(archivo.fileno())

        except FileExistsError as e:
            raise EjecucionEnCurso(
                "Otra ejecución adquirió el bloqueo "
                "casi al mismo tiempo."
            ) from e
        
        except OSError:
            self.ruta.unlink(missing_ok=True)
            raise
        
        self.adquirido = True
        return self

    def _evaluar_bloqueo_existente(self) -> None:
        try:
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
            pid = int(datos["pid"])
            inicio = datetime.fromisoformat(datos["inicio"])
            creacion_guardada = datos.get("creacion_proceso")

        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            self._evaluar_bloqueo_corrupto()
            return
        if _mismo_proceso_activo(
            pid,
            creacion_guardada,
        ):
            raise EjecucionEnCurso(
                "Ejecución activa detectada "
                f"(PID {pid}, desde {inicio.isoformat()})."
            )

        self.ruta.unlink(missing_ok=True)

    def _evaluar_bloqueo_corrupto(self) -> None:
        """Solo elimina un lock corrupto cuando ya es antiguo."""
    
        try:
            fecha_modificacion = datetime.fromtimestamp(
            self.ruta.stat().st_mtime
        )
        except OSError as e:
            raise EjecucionEnCurso(
                "Existe un archivo de bloqueo ilegible "
                "y no fue posible comprobar su antigüedad."
            ) from e
    
        antiguedad = datetime.now() - fecha_modificacion
    
        if antiguedad < self.max:
            raise EjecucionEnCurso(
                "Existe un archivo de bloqueo reciente, "
                "pero su contenido está corrupto o incompleto."
            )
    
        self.ruta.unlink(missing_ok=True)

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        if self.adquirido:
            self.ruta.unlink(missing_ok=True)
            self.adquirido = False

def _creacion_proceso(pid: int) -> float | None:
    try:
        return psutil.Process(pid).create_time()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

"""
Verifica si un PID corresponde a un proceso activo.
En Windows, os.kill solo soporta un subconjunto de señales (SIGTERM, CTRL_C_EVENT, CTRL_BREAK_EVENT);
Ahora se usa psutil.pid_exists(), que funciona de forma consistente en Windows, Linux y macOS.
"""
def _mismo_proceso_activo(
    pid: int,
    creacion_guardada: float | int | str | None,
) -> bool:
    if not psutil.pid_exists(pid):
        return False

    if creacion_guardada is None:
        return True

    try:
        creacion_actual = psutil.Process(pid).create_time()
        return abs(
            creacion_actual - float(creacion_guardada)
        ) < 1.0
    except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError, TypeError):
        return psutil.pid_exists(pid)