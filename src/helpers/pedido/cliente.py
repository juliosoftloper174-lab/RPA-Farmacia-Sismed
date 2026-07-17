from time import sleep

from uiautomation import EditControl, SendKeys

from src.helpers.comun.windows import get_registro_pedido_window


def seleccionar_cliente(dni: str) -> bool:
    ventana = get_registro_pedido_window()

    txt_cliente: EditControl = ventana.EditControl(Name="TxtCliente")
    valor_inicial = txt_cliente.GetValuePattern().Value

    txt_dni: EditControl = ventana.EditControl(Name="TxtDNICli")
    sleep(0.2)
    txt_dni.SetFocus()
    sleep(0.2)
    txt_dni.SendKeys(dni)
    sleep(0.5)
    SendKeys("{Enter}")

    valor_final = ""
    for _ in range(8):
        sleep(0.5)
        valor_final = txt_cliente.GetValuePattern().Value
        if valor_final:
            break

    return valor_final != valor_inicial
