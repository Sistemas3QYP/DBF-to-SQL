from __future__ import annotations
import argparse
import sys
from pathlib import Path
from uuid import uuid4
from .bloqueo_ejecucion import BloqueoEjecucion
from .configuracion import cargar_configuracion
from .excepciones import (
    EjecucionEnCurso,
    ErrorCargaStaging,
    ErrorConfiguracion,
    ErrorConexionFoxPro,
    ErrorConexionSQL,
    ErrorConsultaFoxPro,
    ErrorSincronizacionSQL,
    ErrorValidacionDatos,
)
from .foxpro_repository import FoxProRepository
from .logging_config import configurar_logging, id_ejecucion as ctx_id_ejecucion
from .sincronizador import Sincronizador
from .sql_repository import SqlRepository

CODIGOS_SALIDA = {
    ErrorConfiguracion: 2,
    ErrorConexionFoxPro: 3,
    ErrorConsultaFoxPro: 3,
    ErrorConexionSQL: 4,
    ErrorValidacionDatos: 5,
    EjecucionEnCurso: 6,
    ErrorCargaStaging: 7,
    ErrorSincronizacionSQL: 7,
}

class ArgumentParserIntegracion(
    argparse.ArgumentParser
):
    """ArgumentParser que traduce errores al código 2."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(
            2,
            f"{self.prog}: error: {message}\n",
        )

def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParserIntegracion(
        description="Sincronización de pedidos SAI (FoxPro → SQL Server)"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al archivo JSON de configuración (ej. config/emp43.json)",
    )
    args = parser.parse_args(argv)

    base = Path(__file__).resolve().parents[1]
    id_ejec = uuid4()
    ctx_id_ejecucion.set(str(id_ejec))

    # Logger provisional hasta conocer la empresa
    logger = configurar_logging("sai", base)

    try:
        cfg = cargar_configuracion(args.config)
        # Reconfigurar logger con el nombre de empresa correcto
        logger = configurar_logging(cfg.empresa, base)

        lock_path = base / "runtime" / f"sincronizacion_{cfg.empresa.lower()}.lock"

        with BloqueoEjecucion(lock_path, cfg.lock_max_minutos):
            resultado = Sincronizador(
                cfg,
                FoxProRepository(cfg),
                SqlRepository(cfg),
                logger,
            ).ejecutar(id_ejec)

            logger.info(
                "Fin correcto | estado=%s | "
                "pedidos_extraídos=%s | "
                "pedidos_insertados=%s | "
                "pedidos_actualizados=%s | "
                "facturas_extraídas=%s | "
                "facturas_actualizadas=%s | "
                "facturas_sin_cambios=%s | "
                "facturas_sin_pedido=%s | "
                "intentos=%s",
                resultado.estado,
                resultado.extraidos,
                resultado.insertados,
                resultado.actualizados,
                resultado.facturas_extraidas,
                resultado.facturas_actualizadas,
                resultado.facturas_sin_cambios,
                resultado.facturas_sin_pedido,
                resultado.intentos,
            )
            return 0

    except KeyboardInterrupt:
        logger.warning(
            "Ejecución interrumpida manualmente."
        )
        return 1
    
    except Exception as e:
        codigo = next(
            (cod for cls, cod in CODIGOS_SALIDA.items() if isinstance(e, cls)),
            1,
        )
        logger.exception(
            "Ejecución fallida | código=%s | "
            "tipo=%s | error=%s",
            codigo,
            type(e).__name__,
            e,
        )
        return codigo

if __name__ == "__main__":
    sys.exit(main())
