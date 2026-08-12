from __future__ import annotations
import time
from typing import Callable, Tuple, TypeVar

T = TypeVar("T")

def ejecutar_con_reintentos(
    func: Callable[[], T],
    maximos: int,
    espera_segundos: int,
    es_transitorio: Callable[[Exception], bool],
    logger,
) -> Tuple[T, int]:
    """
    Ejecuta func() con hasta `maximos` intentos.
    Solo reintenta si es_transitorio(exc) es True.
    Devuelve (resultado, número_de_intento_exitoso).
    """
    ultimo_error: Exception | None = None
    for intento in range(1, maximos + 1):
        try:
            return func(), intento
        except Exception as e:
            ultimo_error = e
            if intento >= maximos or not es_transitorio(e):
                raise
            logger.warning(
                "Intento %s/%s falló; reintento en %ss: %s",
                intento,
                maximos,
                espera_segundos,
                e,
            )
            time.sleep(espera_segundos)

    # No debería alcanzarse, pero por seguridad
    assert ultimo_error is not None
    raise ultimo_error