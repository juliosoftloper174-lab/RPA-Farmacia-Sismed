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

    backup_window = WindowControl(searchDepth=1, Name="Backups Automátic")
    if backup_window.Exists(maxSearchSeconds=0):
        logger.warning("Backup detectado. Esperando que finalice...")
        for i in range(15):
            sleep(60)
            if not backup_window.Exists(maxSearchSeconds=0):
                logger.info("Backup finalizado. Continuando...")
                break
            logger.warning(f"Backup en curso... ({i+1}/15, ~{i+1} min)")
        else:
            logger.critical("Backup no finalizó después de 15 min. Saliendo.")
            exit()

    LOGIN_WINDOW = WindowControl(Name="Acceso al Sistema")
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
