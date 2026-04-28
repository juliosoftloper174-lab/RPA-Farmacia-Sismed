"""CARGA DE VARIABLES DE ENTORNO y proximamente otras configuraciones."""

from os import environ

from dotenv import load_dotenv

load_dotenv()

SISMED_EXE: str = environ["SISMED_EXE"]
