from os import environ
from time import sleep


from dotenv import load_dotenv
from uiautomation import (
    EditControl,
    GroupControl,
    WindowControl,
    PaneControl,
    ButtonControl,
    Click,
    SendKeys,
)

from ..sidmed.ingreso import (
    seleccionar_combo_por_texto,
    seleccionar_combo_por_texto_con_autoenter,
)
from ..models.forma_pago import FormaPago
from ..helpers.cliente import seleccionar_cliente
from ..helpers.diagnosticos import rellenar_diagnosticos
from ..helpers.farmacia import seleccionar_farmacia_por_codigo
from ..helpers.input import escribir_input
from ..helpers.producto import agregar_productos
from ..models.pedido import Pedido
from ..sidmed._login import login

load_dotenv()

username = environ["SISMED_USERNAME"]
password = environ["SISMED_PASSWORD"]

MINSA_SISMED_WINDOW: WindowControl = WindowControl(searchDepth=1, Name="MINSA SISMED")
MINSA_SISMED_PANEL: PaneControl = MINSA_SISMED_WINDOW.PaneControl(
    searchDepth=1, Name="MINSA SISMED"
)
MAIN_WINDOW: WindowControl = MINSA_SISMED_PANEL.WindowControl(
    searchDepth=1, Name="Menu Principal"
)
SYSTEM_INFO_PANEL: PaneControl = MAIN_WINDOW.PaneControl(
    searchDepth=1, foundIndex=1, Name=""
)

FARMACIA_WINDOW: WindowControl = WindowControl(
    searchDepth=1, Name="FARMACIA - MINSA SISMED C:\sismedv2_hospitalrioja ()"
)
FARMACIA_PANEL: PaneControl = FARMACIA_WINDOW.PaneControl(
    searchDepth=1, Name="FARMACIA - MINSA SISMED C:\sismedv2_hospitalrioja ()"
)
CONTROL_FARMARCIA_WINDOW: WindowControl = FARMACIA_PANEL.WindowControl(
    searchDepth=1, Name="Control de Farmacia"
)
MODULO_CONTROL_FARMACIA_PANEL: PaneControl = CONTROL_FARMARCIA_WINDOW.PaneControl(
    searchDepth=1, foundIndex=1, Name=""
)
REGISTRO_PEDIDO_WINDOW: WindowControl = FARMACIA_PANEL.WindowControl(
    searchDepth=1, Name="Registro de Pedido"
)
BARRA_GROUP: GroupControl = REGISTRO_PEDIDO_WINDOW.GroupControl(
    searchDepth=1, Name="Barra"
)


def navegar_a_pedidos(pedido: Pedido) -> None:
    """NOTE: SendKey and Senkeys works weird here."""

    SYSTEM_INFO_PANEL.SendKeys("{RIGHT}{Enter}")

    seleccionar_farmacia_por_codigo(pedido.farmacia.codigo)
    sleep(0.3)

    # NOTE: Go to "Procesos" Module.
    for _ in range(2):
        MODULO_CONTROL_FARMACIA_PANEL.SendKeys("{DOWN}")

    OPTIONS_PANEL: PaneControl = CONTROL_FARMARCIA_WINDOW.PaneControl(
        searchDepth=1, foundIndex=2, Name=""
    )  # NOTE: Just appear after selectinf "Procesos" Module.

    OPTIONS_PANEL.SendKey("{TAB}")
    OPTIONS_PANEL.SendKeys("{Enter}")
    REGISTRO_PEDIDO_WINDOW.Exists()
    return None


def rellenar_fua(pedido: Pedido) -> None:
    input_fua = REGISTRO_PEDIDO_WINDOW.EditControl(searchDepth=1, Name="Txtfua")
    escribir_input(input_fua, pedido.fua)


def rellenar_ups(codigo_ups: str) -> None:
    # Abrir modal UPS (click ciego)
    sleep(1)
    Click(730, 388)
    sleep(1)

    # Buscar por código
    Click(1090, 345)
    sleep(0.5)

    # Escribir código
    SendKeys(codigo_ups)
    sleep(1)

    # Botón aceptar
    aceptar = REGISTRO_PEDIDO_WINDOW.ButtonControl(Name="Aceptar")

    if not aceptar.Exists(3):
        # fallback por si está en otra ventana/modal
        aceptar = ButtonControl(Name="Aceptar")

    if aceptar.Exists(3):
        aceptar.Click()
    else:
        raise Exception("No se encontró botón 'Aceptar' en UPS")


def manejar_forma_pago(pedido: Pedido) -> None:
    tipo = pedido.forma_pago

    if tipo == FormaPago.SIS:
        rellenar_fua(pedido)

    elif tipo == FormaPago.INTERVENCION_SANITARIA:
        # ⚠️ asegúrate que exista este atributo en tu modelo Pedido
        rellenar_ups(pedido.ups_codigo)

    elif tipo == FormaPago.CONTADO:
        # NOTE: No hace nada en especial, pero lo pongo por si acaso.
        pass

    else:
        raise ValueError(f"Forma de pago no soportada: {pedido.forma_pago.value}")


def rellenar_cabecera(pedido: Pedido) -> None:

    # Forma de pago
    seleccionar_combo_por_texto_con_autoenter("CboDato", pedido.forma_pago.value)

    # ✅ NUEVA LÓGICA
    manejar_forma_pago(pedido)

    # Tipo receta
    seleccionar_combo_por_texto("cmbTipoReceta", pedido.tipo_receta.value)

    # Cliente
    Click(770, 410)
    seleccionar_cliente(pedido.cliente.codigo)

    # Prescriptor
    presc: EditControl = REGISTRO_PEDIDO_WINDOW.EditControl(Name="TxtColPresc")
    escribir_input(presc, pedido.prescriptor.codigo)
    presc.SendKeys("{Enter}")

    # Diagnósticos
    rellenar_diagnosticos(
        REGISTRO_PEDIDO_WINDOW, [d.codigo for d in pedido.diagnosticos]
    )
    return None


def guardar() -> None:
    CmdSave: ButtonControl = BARRA_GROUP.ButtonControl(searchDepth=1, Name="CmdSave")
    CmdSave.Click()
    sleep(0.3)
    return None


def procesar_pedido(pedido: Pedido) -> None:

    login(username, password)
    navegar_a_pedidos(pedido)
    rellenar_cabecera(pedido)

    # Productos
    agregar_productos(tuple(pedido.productos))
    guardar()
    sleep(0.3)
    return sleep(0.5)


def procesar_pedidos(pedidos: tuple[Pedido, ...]) -> None:
    for pedido in pedidos:
        procesar_pedido(pedido)
    return None
