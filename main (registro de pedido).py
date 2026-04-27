from datetime import datetime
from os import environ
from subprocess import Popen
from time import sleep

import uiautomation as auto
from dotenv import load_dotenv
from uiautomation import PaneControl, TableControl, WindowControl

# =========================================================
# 🔹 CARGA DE VARIABLES DE ENTORNO
# =========================================================
load_dotenv()

SISMED_EXE: str = environ["SISMED_EXE"]

# =========================================================
# 🔹 FUNCIONES REUTILIZABLES
# =========================================================


def esperar_ventana(nombre: str, timeout: int = 10) -> WindowControl:
    ventana = WindowControl(searchDepth=4, Name=nombre)
    if not ventana.Exists(timeout):

        raise Exception(f"No se encontró la ventana: {nombre}")
    return ventana


def seleccionar_combo_click_ciego(combo, posicion: int):
    if not combo.Exists(5):
        raise Exception("ComboBox no encontrado")

    combo.SetFocus()
    sleep(0.3)

    for _ in range(posicion):
        combo.Click()
        sleep(0.3)

        auto.SendKeys("{Down}")
        sleep(0.2)

    auto.SendKeys("{Enter}")


def escribir_input(control, texto: str):
    if not control.Exists(5):
        raise Exception("Input no encontrado")

    control.SetFocus()
    sleep(0.2)
    control.SendKeys(texto)


def seleccionar_cliente(nombre_cliente: str):
    auto.Click(770, 410)
    sleep(0.5)

    ventana_cliente = WindowControl(searchDepth=4, Name="Seleccionar Clientes")
    ventana_cliente.Exists(5)

    txt_busca = ventana_cliente.EditControl(Name="TxtBusca")
    txt_busca.SetFocus()
    sleep(0.2)

    txt_busca.SendKeys(nombre_cliente)
    sleep(0.5)

    auto.SendKeys("{Enter}")
    sleep(0.5)

    boton_seleccionar = ventana_cliente.ButtonControl(Name="Seleccionar")
    boton_seleccionar.Click()


# 👇 ESTA FUNCIÓN VA AFUERA


def rellenar_diagnosticos(registro_window, lista_diagnosticos):

    if len(lista_diagnosticos) == 0:
        raise Exception("Debe haber al menos 1 diagnóstico")

    inputs = [
        registro_window.EditControl(Name="TxtCodCIE"),
        registro_window.EditControl(Name="TxtCodCIE1"),
        registro_window.EditControl(Name="TxtCodCIE2"),
    ]

    for i, diag in enumerate(lista_diagnosticos):
        if i >= len(inputs):
            break

        print(f"Escribiendo diagnóstico {i+1}: {diag}")

        escribir_input(inputs[i], diag)
        sleep(0.3)

        # 🔥 SIEMPRE Enter (incluido el último)
        auto.SendKeys("{Enter}")
        sleep(0.4)

    # =====================================================
    # 🔥 LIMPIAR FILAS VACÍAS (justo después del último Enter)
    # =====================================================

    print("[BOT] Limpiando filas vacías...")

    auto.SendKeys("{CONTROL}{DEL}")
    sleep(0.6)

    auto.SendKeys("{CONTROL}{DEL}")
    sleep(0.6)


def obtener_nombre_base(nombre_completo: str) -> str:
    return nombre_completo.split("-")[0].strip()


# 🔹 FLUJO PRINCIPAL DEL BOT
# =========================================================


def main() -> None:
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
    seleccionar_combo_click_ciego(combo_formadepago, 9)

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

    # Vayamos a agregar productos de la cabecera_detallle

    auto.SendKeys("{CONTROL}{INSERT}")
    auto.SendKeys("{Enter}")

    ventana_medicamentos = esperar_ventana("Seleccionar medicamento")

    txt_busca = ventana_medicamentos.EditControl(Name="TxtBusca")

    # escribir_input(txt_busca, "ACIDO ACETILSALICILICO")

    nombre_completo = "ACIDO ACETILSALICILICO - 500 mg - TABLET -"
    nombre_base = obtener_nombre_base(nombre_completo)

    # 🔹 buscar con nombre base
    escribir_input(txt_busca, nombre_base)

    sleep(0.3)
    auto.SendKeys("{Enter}")
    sleep(0.3)

    # 🔹 leer tabla
    table_med = TableControl(Name="GrdMed")
    view_1 = table_med.TableControl(searchDepth=1, Name="View 1")

    items_len = 17

    for i in range(items_len):
        index = i + 1
        row = view_1.CustomControl(searchDepth=1, Name=str(index))

        description_cell = row.DataItemControl(searchDepth=1, foundIndex=1)
        description_edit = description_cell.EditControl(searchDepth=1, Name="Text1")
        description_value = description_edit.GetValuePattern().Value

        print(description_value)  # debug opcional

        # 🔹 comparar EXACTAMENTE con el nombre completo
        if description_value.strip().lower() == nombre_completo.strip().lower():
            print("✔ encontrado correcto")

            row.Click()  # seleccionar fila
            auto.SendKeys("{Enter}")  # confirmar

            break  # 🔥 detener el loop cuando lo encuentra

        sleep(0.3)


# =========================================================
# 🔹 EJECUCIÓN
# =========================================================
if __name__ == "__main__":
    main()
