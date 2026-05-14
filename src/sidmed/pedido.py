from random import randint

from time import sleep


from uiautomation import EditControl, PaneControl, ButtonControl, Click, SendKeys

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
from ..helpers.windows import *
from ..reportes.excel_schema import crear_row_pedido
from ..reportes.excel_writer import (
    guardar_movimientos,
    obtener_siguiente_numero_procesado,
)
from ..logger import logger
from ..config import SISMED_PASSWORD, SISMED_USERNAME


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


# def extraer_correlativo_farmacia() -> None:
# esta funcion debe de generar un correlativo falso para poder registarlo en el excel como lo hace ingreso y salida solo que aqui en pedido no me lo da por el ambiente de prueba pero si deberia de hacerlo en un futuro


def extraer_correlativo_farmacia() -> str:
    # has que genere un correlativo rando para poderlo meter en el excel
    correlativo = randint(1, 1000)
    return correlativo


def cerrar_sismed_pedido() -> None:

    # Click 1
    Click(1168, 188)
    sleep(3)

    # Click 2
    Click(1189, 214)
    sleep(3)

    # Click 3
    Click(1585, 15)
    sleep(3)

    # Click 4
    Click(1585, 15)
    sleep(3)

    return None


def procesar_pedido(pedido: Pedido) -> str:

    login(SISMED_USERNAME, SISMED_PASSWORD)
    navegar_a_pedidos(pedido)
    rellenar_cabecera(pedido)

    # Productos
    agregar_productos(tuple(pedido.productos))
    guardar()
    sleep(0.3)
    correlativo: str = extraer_correlativo_farmacia()
    sleep(5)
    cerrar_sismed_pedido()
    sleep(0.5)
    return str(correlativo)


def procesar_pedidos(pedidos: tuple[Pedido, ...]) -> None:
    k_salud_correlativo = randint(1_000_000, 9_999_999)
    numero_procesado = obtener_siguiente_numero_procesado()
    rows: list[dict] = []

    for pedido in pedidos:
        try:
            correlativo = procesar_pedido(pedido)
            row = crear_row_pedido(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=k_salud_correlativo,
                correlativo_sismed=correlativo,
                pedido=pedido,
                estado="OK",
            )
        except Exception as exc:
            logger.exception("Error procesando un pedido.")
            row = crear_row_pedido(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=k_salud_correlativo,
                correlativo_sismed="",
                pedido=pedido,
                estado="ERROR",
                error=str(exc),
            )

        rows.append(row)
        k_salud_correlativo += 1
        numero_procesado += 1

    if rows:
        guardar_movimientos(rows)

    return None
