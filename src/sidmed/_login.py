from subprocess import Popen

from uiautomation import SendKeys, WindowControl, ButtonControl

from src.config import SISMED_EXE

MINSA_SISMED_WINDOW: WindowControl = WindowControl(searchDepth=1, Name="MINSA SISMED")
LOGIN_WINDOW: WindowControl = WindowControl(Name="Acceso al Sistema")


def login(username: str, password: str) -> None:
    SendKeys("{Win}d")

    # NOTE: Thsi fails, windows dies for some reason.
    # if MINSA_SISMED_WINDOW.Exists(maxSearchSeconds=0):
    #    MINSA_SISMED_WINDOW.Maximize()
    #     return cerrar_ventana_inicial()

    if not LOGIN_WINDOW.Exists(maxSearchSeconds=0):
        Popen(SISMED_EXE)

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
