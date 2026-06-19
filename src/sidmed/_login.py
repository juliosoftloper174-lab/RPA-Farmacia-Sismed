from subprocess import Popen
from time import sleep

from uiautomation import SendKeys, WindowControl, ButtonControl
from loguru import logger
from src.config import SISMED_EXE


def login(username: str, password: str) -> None:
    SendKeys("{Win}d")

    LOGIN_WINDOW = WindowControl(Name="Acceso al Sistema")
    if not LOGIN_WINDOW.Exists(maxSearchSeconds=0):
        Popen(SISMED_EXE)
        sleep(3)
        LOGIN_WINDOW = WindowControl(Name="Acceso al Sistema")

    if WindowControl(searchDepth=1, Name="Backups Automátic").Exists():
        logger.critical("SISMED: Backuping... Wait for it to finish and retry later.")
        exit()

    LOGIN_WINDOW.EditControl(Name="txtUsuario").SendKeys(username)
    LOGIN_WINDOW.EditControl(Name="txtClave").SendKeys(password)
    LOGIN_WINDOW.ButtonControl(Name="Aceptar").Click()

    return cerrar_ventana_inicial()


def cerrar_ventana_inicial() -> None:
    ventana: WindowControl = WindowControl(Name="Productos Vencidos y por Vencer")
    if ventana.Exists():
        exit_button: ButtonControl = ventana.ButtonControl(Name="Salir")
        exit_button.Click()
    return None
