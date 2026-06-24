from time import sleep

from uiautomation import EditControl, SendKeys
from src.helpers.windows import get_registro_pedido_window


def seleccionar_cliente(dni: str) -> None:
    ventana = get_registro_pedido_window()
    txt_dni: EditControl = ventana.EditControl(Name="TxtDNICli")
    sleep(0.2)
    txt_dni.SetFocus()
    sleep(0.2)
    txt_dni.SendKeys(dni)
    sleep(0.5)
    SendKeys("{Enter}")
