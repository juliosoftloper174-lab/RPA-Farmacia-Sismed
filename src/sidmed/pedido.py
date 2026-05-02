from os import environ
from subprocess import Popen
from time import sleep

import uiautomation as auto
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


def procesar_pedido(pedido: Pedido) -> None:

    # =====================================================
    # 1. 🔐 LOGIN
    # =====================================================
    print("Abriendo SISMED...")
    Popen(SISMED_EXE)

    login_window = esperar_ventana("Acceso al Sistema")

    escribir_input(
        login_window.EditControl(Name="txtUsuario"), environ["SISMED_USERNAME"]
    )

    escribir_input(
        login_window.EditControl(Name="txtClave"), environ["SIDMED_PASSWORD"]
    )

    login_window.ButtonControl(Name="Aceptar").Click()

    # =====================================================
    # 2. ❌ CERRAR POPUP
    # =====================================================
    productos_window = WindowControl(
        searchDepth=3, Name="Productos Vencidos y por Vencer"
    )

    if productos_window.Exists():
        productos_window.ButtonControl(Name="Salir").Click()

    # =====================================================
    # 3. 📂 NAVEGACIÓN
    # =====================================================
    panel = PaneControl(foundIndex=1, searchDepth=5)
    panel.SetFocus()

    seleccionar_farmacia_por_codigo(pedido.farmacia.codigo)

    sleep(0.3)
    auto.Click(48, 122)

    sleep(0.3)
    auto.Click(355, 115)
    auto.SendKeys("{Enter}")

    # =====================================================
    # 4. 🧾 REGISTRO DE PEDIDO
    # =====================================================
    ventana = esperar_ventana("Registro de Pedido")

    # Forma de pago
    combo = ventana.ComboBoxControl(Name="CboDato")
    seleccionar_combo_click_ciego(combo, pedido.forma_pago.value)

    # FUA
    escribir_input(ventana.EditControl(Name="Txtfua"), pedido.fua)

    # Tipo receta
    seleccionar_combo_click_ciego(ventana.ComboBoxControl(Name="cmbTipoReceta"), 3)

    # Cliente
    auto.Click(770, 410)
    seleccionar_cliente(pedido.cliente.nombre)

    # Prescriptor
    presc = ventana.EditControl(Name="TxtColPresc")
    escribir_input(presc, pedido.prescriptor.codigo)
    auto.SendKeys("{Enter}")

    # Diagnósticos
    rellenar_diagnosticos(ventana, [d.codigo for d in pedido.diagnosticos])

    # Productos
    agregar_productos(tuple(pedido.productos))

    return sleep(0.5)


def procesar_pedidos(pedidos: tuple[Pedido, ...]) -> None:
    for pedido in pedidos:
        procesar_pedido(pedido)
    return None
