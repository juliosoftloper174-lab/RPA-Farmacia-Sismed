"""CARGA DE VARIABLES DE ENTORNO y proximamente otras configuraciones."""

from os import environ

from dotenv import load_dotenv

load_dotenv()

SISMED_EXE: str = environ["SISMED_EXE"]
SISMED_USERNAME: str = environ["SISMED_USERNAME"]
SISMED_PASSWORD: str = environ["SISMED_PASSWORD"]

DB_SERVER: str = environ["DB_SERVER"]
DB_NAME: str = environ["DB_NAME"]
DB_USER: str = environ["DB_USER"]
DB_PASS: str = environ["DB_PASS"]
