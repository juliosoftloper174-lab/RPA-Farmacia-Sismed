from subprocess import Popen

from uiautomation import SendKeys, WindowControl, ButtonControl

from src.config import SISMED_EXE


def login(username: str, password: str) -> None:
    SendKeys("{Win}d")
    Popen(SISMED_EXE)

    login_window: WindowControl = WindowControl(Name="Acceso al Sistema")
    login_window.EditControl(Name="txtUsuario").SendKeys(username)
    login_window.EditControl(Name="txtClave").SendKeys(password)
    login_window.ButtonControl(Name="Aceptar").Click()

    return cerrar_ventana_inicial()


def cerrar_ventana_inicial() -> None:
    ventana: WindowControl = WindowControl(Name="Productos Vencidos y por Vencer")
    if ventana.Exists():
        exit_button: ButtonControl = ventana.ButtonControl(Name="Salir")
        exit_button.Click()
    return None
