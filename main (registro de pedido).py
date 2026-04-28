from os import environ
from subprocess import Popen
from time import sleep

import uiautomation as auto
from uiautomation import PaneControl, TableControl, WindowControl

from src.config import SISMED_EXE
from src.helpers.cliente import seleccionar_cliente
from src.helpers.combo import seleccionar_combo_click_ciego
from src.helpers.diagnosticos import rellenar_diagnosticos
from src.helpers.input import escribir_input
from src.helpers.ventana import esperar_ventana
from src.models.producto import Producto

# =========================================================
# 🔹 FUNCIONES REUTILIZABLES
# =========================================================


def obtener_nombre_base(nombre_completo: str) -> str:
    return nombre_completo.split("-")[0].strip()


# 🔹 FLUJO PRINCIPAL DEL BOT
# =========================================================


def agregar_producto(producto: Producto) -> None:

    auto.SendKeys("{CONTROL}{INSERT}")
    auto.SendKeys("{Enter}")

    ventana_medicamentos = esperar_ventana("Seleccionar medicamento")

    txt_busca = ventana_medicamentos.EditControl(Name="TxtBusca")

    # escribir_input(txt_busca, "ACIDO ACETILSALICILICO")

    nombre_completo = producto.nombre
    nombre_base = obtener_nombre_base(nombre_completo)

    # 🔹 buscar con nombre base
    escribir_input(txt_busca, nombre_base)

    sleep(1)
    txt_busca.SendKeys("{Enter}")
    sleep(1)

    # 🔹 leer tabla
    table_med = TableControl(Name="GrdMed")
    view_1 = table_med.TableControl(searchDepth=1, Name="View 1")

    items_len = 17

    # NOTE: For some weird reason, first row is 2nd row, because first one has a fixed value, idk why or if this means trouble in the future.

    elements = []  # NOTE: Para debugear, no sirve en produccion
    for i in range(items_len):
        index = i + 1
        row = view_1.CustomControl(searchDepth=1, Name=str(index))

        description_cell = row.DataItemControl(searchDepth=1, foundIndex=1)
        description_edit = description_cell.EditControl(searchDepth=1, Name="Text1")
        description_value = description_edit.GetValuePattern().Value

        if not description_value:
            continue

        elements.append((row, description_value))

        print(f"{description_value = }")  # debug opcional

        # 🔹 comparar EXACTAMENTE con el nombre completo
        if description_value.strip().lower() == nombre_completo.strip().lower():
            print("✔ encontrado correcto")

            row.Click()  # seleccionar fila
            row.SendKeys("{Enter}")  # confirmar

            break  # 🔥 detener el loop cuando lo encuentra

        sleep(1)

    return None


def agregar_productos(productos: tuple[Producto, ...]):
    for producto in productos:
        agregar_producto(producto)
    return None


def main(productos: tuple[Producto, ...]) -> None:
    """
    TODO: Backup in github.
    TODO: Use parameters
    TODO: Use dataclasses
    TODO: Extract away complex logic, do modules and import them here.
    """

    # =====================================================
    # 1. 🔐 ABRIR SISTEMA Y HACER LOGIN
    # =====================================================
    print("Abriendo SISMED...")
    Popen(SISMED_EXE)

    login_window = esperar_ventana("Acceso al Sistema")

    print("Ingresando credenciales...")

    escribir_input(
        login_window.EditControl(Name="txtUsuario"), environ["SISMED_USERNAME"]
    )
    escribir_input(
        login_window.EditControl(Name="txtClave"), environ["SIDMED_PASSWORD"]
    )

    login_window.ButtonControl(Name="Aceptar").Click()

    # =====================================================
    # 2. ❌ CERRAR VENTANA INICIAL
    # =====================================================
    productos_window = WindowControl(
        searchDepth=3, Name="Productos Vencidos y por Vencer"
    )

    if productos_window.Exists():
        print("Cerrando ventana de productos...")
        productos_window.ButtonControl(Name="Salir").Click()

    # =====================================================
    # 3. 📂 NAVEGACIÓN EN EL MENÚ
    # =====================================================
    print("Navegando al módulo de ingresos...")

    panel_window = PaneControl(foundIndex=1, searchDepth=5)
    panel_window.SetFocus()

    auto.Click(440, 115)  # Control de farmacia
    sleep(0.3)
    auto.SendKeys("{Enter}")

    auto.SendKeys(
        "{Enter}"
    )  # seleccionar farmacia, aqui segun se debe de leer la base de datos y aplicar logica para que selecione 1 de las 6

    sleep(0.3)
    auto.Click(48, 122)  # Procesos

    sleep(0.3)
    auto.Click(355, 115)  # Pedido de registro
    auto.SendKeys("{Enter}")

    # =====================================================
    # 4. 📝 REGISTRO DE PEDIDO
    # =====================================================
    Registro_pedido = esperar_ventana("Registro de Pedido")

    # 🔹 Forma de pago (posición 9: sis)

    combo_formadepago = Registro_pedido.ComboBoxControl(Name="CboDato")
    fila_bd = {"forma_pago_id": 9}

    id_forma_pago = fila_bd["forma_pago_id"]

    mapa_forma_pago = {
        0: 0,  # Contado (default)
        1: 1,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 6,  # Intervención Sanitaria
        7: 7,
        8: 8,
        9: 9,  # SIS
        10: 10,
    }

    posicion = mapa_forma_pago.get(id_forma_pago)

    if posicion is None:
        raise Exception(f"Forma de pago no mapeada: {id_forma_pago}")

    seleccionar_combo_click_ciego(combo_formadepago, posicion)

    # combo_formadepago = Registro_pedido.ComboBoxControl(Name="CboDato")
    # seleccionar_combo_click_ciego(combo_formadepago, 9)

    # 🔹 FUA
    fua_input = Registro_pedido.EditControl(Name="Txtfua")
    escribir_input(fua_input, "786636652")

    # 🔹 Tipo de receta (posición 3: sin numero)

    combo_tipo_receta = Registro_pedido.ComboBoxControl(Name="cmbTipoReceta")
    seleccionar_combo_click_ciego(combo_tipo_receta, 3)

    # meteler el cliente:
    # clcik en 770 y 410
    # ABAD CARDENAS, SELOMIT ABIGAIL este es el nombre del cliente

    auto.Click(770, 410)  # click en el botom que abre el selecionar cliente

    # en el txt de "TxtBusca" see debe de escribir el nombre del cliente

    seleccionar_cliente("ABAD CARDENAS, SELOMIT ABIGAIL")

    # colocar Prescriptor
    Presc_imput = Registro_pedido.EditControl(Name="TxtColPresc")
    escribir_input(Presc_imput, "14571")
    auto.SendKeys("{Enter}")

    # los dig
    # 🔹 Diagnósticos
    diagnosticos = ["R100", "R05X", "K750"]
    rellenar_diagnosticos(Registro_pedido, diagnosticos)

    agregar_productos(productos)
    return None


# =========================================================
# 🔹 EJECUCIÓN
# =========================================================
if __name__ == "__main__":
    productos = (
        Producto(nombre="ACIDO ACETILSALICILICO - 500 mg - TABLET -"),
        Producto(nombre="ACIDO ACETILSALICILICO - 100 mg - TABLET -"),
    )
    main(productos)
    # # GrdDeta is the other table
