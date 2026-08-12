from __future__ import annotations
import logging
from contextvars import ContextVar
from datetime import date
from pathlib import Path

id_ejecucion = ContextVar("id_ejecucion", default="-")

class ContextFilter(logging.Filter):
    def filter(self, record):
        record.id_ejecucion = id_ejecucion.get()
        return True

def configurar_logging(empresa: str, base: Path) -> logging.Logger:
    """
    Crea (o reutiliza) un logger por empresa.
    Genera un archivo diario: logs/{empresa}_{YYYY-MM-DD}.log
    """
    logs_dir = base / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger_name = f"sai.{empresa.lower()}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Evitar handlers duplicados si se invoca más de una vez
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(id_ejecucion)s | %(module)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        logs_dir / f"{empresa.lower()}_{date.today().isoformat()}.log",
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    file_handler.addFilter(ContextFilter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.addFilter(ContextFilter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger