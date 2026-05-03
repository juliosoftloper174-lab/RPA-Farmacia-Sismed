from os import environ
from subprocess import Popen
from time import sleep

import uiautomation as auto
from dotenv import load_dotenv
from uiautomation import PaneControl, WindowControl

from ..config import SISMED_EXE
from ..helpers.cliente import seleccionar_cliente
from ..helpers.combo import seleccionar_combo_click_ciego
from ..helpers.diagnosticos import rellenar_diagnosticos
from ..helpers.farmacia import seleccionar_farmacia_por_codigo
from ..helpers.input import escribir_input
from ..helpers.producto import agregar_productos
from ..helpers.ventana import esperar_ventana
from ..models.cliente import Cliente
from ..models.diagnostico import Diagnostico
from ..models.farmacia import Farmacia
from ..models.forma_pago import FormaPago
from ..models.pedido import Pedido
from ..models.prescriptor import Prescriptor
from ..models.producto import Producto
from ..sidmed._login import login
from ..sidmed._login import cerrar_ventana_inicial
from src.models import pedido

from src.helpers import ventana

load_dotenv()

username = environ["SISMED_USERNAME"]
password = environ["SISMED_PASSWORD"]


def navegar_a_pedidos(pedido: Pedido):
    auto.SendKeys("{RIGHT}")
    auto.SendKeys("{Enter}")
    sleep(0.3)

    seleccionar_farmacia_por_codigo(pedido.farmacia.codigo)

    sleep(0.3)
    auto.SendKeys("{DOWN}")
    sleep(0.3)
    auto.SendKeys("{DOWN}")
    sleep(0.3)

    auto.Click(360, 100)
    sleep(0.3)
    auto.SendKeys("{Enter}")


def r_cabecera(ventana, pedido: Pedido):

    # Forma de pago
    combo = ventana.ComboBoxControl(Name="CboDato")
    seleccionar_combo_click_ciego(combo, pedido.forma_pago.value)

    # FUA
    escribir_input(ventana.EditControl(Name="Txtfua"), pedido.fua)

    # Tipo receta
    seleccionar_combo_click_ciego(ventana.ComboBoxControl(Name="cmbTipoReceta"), 3)

    # Cliente
    auto.Click(770, 410)
    seleccionar_cliente(pedido.cliente.codigo)

    # Prescriptor
    presc = ventana.EditControl(Name="TxtColPresc")
    escribir_input(presc, pedido.prescriptor.codigo)
    auto.SendKeys("{Enter}")

    # Diagnósticos
    rellenar_diagnosticos(ventana, [d.codigo for d in pedido.diagnosticos])


def guardar():
    CmdSave = auto.ButtonControl(Name="CmdSave")
    CmdSave.Click()
    sleep(0.3)


def procesar_pedido(pedido: Pedido) -> None:

    login(username, password)
    cerrar_ventana_inicial()
    navegar_a_pedidos(pedido)
    ventana = esperar_ventana("Registro de Pedido")
    r_cabecera(ventana, pedido)

    # Productos
    agregar_productos(tuple(pedido.productos))
    guardar()
    return sleep(0.5)


def procesar_pedidos(pedidos: tuple[Pedido, ...]) -> None:
    for pedido in pedidos:
        procesar_pedido(pedido)
    return None
