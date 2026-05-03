from time import sleep

from uiautomation import ButtonControl, Click, EditControl, SendKeys, WindowControl


def seleccionar_cliente(codigo_cliente: str) -> None:
    Click(770, 410)
    sleep(0.5)

    ventana_cliente: WindowControl = WindowControl(
        searchDepth=4, Name="Seleccionar Clientes"
    )
    ventana_cliente.Exists(5)

    # 🔹 Cambiar a búsqueda por código
    Click(760, 340)
    sleep(0.3)

    txt_busca: EditControl = ventana_cliente.EditControl(Name="TxtBusca")
    txt_busca.SetFocus()
    sleep(0.2)

    # 🔹 Ahora sí: enviamos código
    txt_busca.SendKeys(codigo_cliente)
    sleep(0.5)

    SendKeys("{Enter}")
    sleep(0.5)

    boton_seleccionar: ButtonControl = ventana_cliente.ButtonControl(Name="Seleccionar")
    boton_seleccionar.Click()
