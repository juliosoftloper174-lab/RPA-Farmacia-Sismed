"""CARGA DE VARIABLES DE ENTORNO y proximamente otras configuraciones."""

from os import environ

from dotenv import load_dotenv

load_dotenv()


def _bool_env(key: str, default: bool = False) -> bool:
    return environ.get(key, str(default)).strip().lower() in ("true", "1", "yes")


SISMED_EXE: str = environ["SISMED_EXE"]
SISMED_USERNAME: str = environ["SISMED_USERNAME"]
SISMED_PASSWORD: str = environ["SISMED_PASSWORD"]

DB_SERVER: str = environ["DB_SERVER"]
DB_NAME: str = environ["DB_NAME"]
DB_USER: str = environ["DB_USER"]
DB_PASS: str = environ["DB_PASS"]

# Control de flujos
procesar_ingresos: bool = _bool_env("PROCESAR_INGRESOS", True)
procesar_salidas: bool = _bool_env("PROCESAR_SALIDAS", True)
procesar_pedidos: bool = _bool_env("PROCESAR_PEDIDOS", True)

# false = salta movimientos con estado de error
procesar_errores: bool = _bool_env("PROCESAR_ERRORES", False)

# Fechas para consulta de movimientos (opcional, fallback en __main__.py)
FECHA_INI: str | None = environ.get("FECHA_INI")
FECHA_FIN: str | None = environ.get("FECHA_FIN")
