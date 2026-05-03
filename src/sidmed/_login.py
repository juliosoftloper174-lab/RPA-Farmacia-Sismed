from subprocess import Popen

from uiautomation import SendKeys, WindowControl

from src.config import SISMED_EXE


def login(username: str, password: str) -> None:
    SendKeys("{Win}d")
    Popen(SISMED_EXE)

    login_window = WindowControl(Name="Acceso al Sistema")
    # login_window.SetFocus()
    # login_window.Exists(10)

    # sleep(3)

    login_window.EditControl(Name="txtUsuario").SendKeys(username)
    login_window.EditControl(Name="txtClave").SendKeys(password)

    login_window.ButtonControl(Name="Aceptar").Click()
    cerrar_ventana_inicial()


def cerrar_ventana_inicial():
    ventana = WindowControl(Name="Productos Vencidos y por Vencer")

    if ventana.Exists():
        ventana.ButtonControl(Name="Salir").Click()
