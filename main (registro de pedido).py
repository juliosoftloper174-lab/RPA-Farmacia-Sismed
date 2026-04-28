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
    auto.SendKeys(str(producto.cantidad))
    auto.SendKeys("{CONTROL}{INSERT}")
    auto.SendKeys("{CONTROL}{DELETE}")
    return None


def agregar_productos(productos: tuple[Producto, ...]):
    for producto in productos:
        agregar_producto(producto)
    return None


def seleccionar_farmacia(nombre_farmacia: str):
    from time import sleep

    import uiautomation as auto

    farmacias = {
        "HOSP. DE RIOJA": 0,
        "HOSP. CENTRAL": 1,
        "DOSIS UNIT.": 2,
        "EMERGENCIA": 3,
        "SOP": 4,
        "UPSS": 5,
    }

    # 🔹 Abrir ventana
    auto.Click(440, 115)
    sleep(0.5)
    auto.SendKeys("{Enter}")
    sleep(0.7)

    ventana = auto.WindowControl(Name="Selección de Farmacias")

    if not ventana.Exists(3):
        raise Exception("No se encontró la ventana")

    ventana.SetActive()
    sleep(0.5)

    # 🔥 recorrer árbol completo (forma compatible)
    filas = []

    for control, depth in auto.WalkControl(ventana):
        # buscamos los "1", "2", "3"... que viste en inspector
        if control.ControlTypeName == "CustomControl" and control.Name.isdigit():
            filas.append(control)

    # ordenar correctamente
    filas.sort(key=lambda x: int(x.Name))

    if not filas:
        raise Exception("No se encontraron filas numeradas")

    # 🔹 índice desde BD
    indice = farmacias.get(nombre_farmacia.upper(), 0)

    if indice >= len(filas):
        raise Exception(f"Índice fuera de rango: {indice}")

    fila = filas[indice]

    # 🔹 interactuar
    try:
        fila.SetFocus()
    except:
        pass

    fila.Click()
    sleep(0.2)

    auto.SendKeys("{Enter}")


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    return texto.replace(" ", "").strip().upper()


def obtener_texto_edit(ctrl):
    """Busca texto dentro de EditControl (Text1)"""
    import uiautomation as auto

    for hijo in ctrl.GetChildren():
        if hijo.ControlType == auto.ControlType.EditControl:
            try:
                vp = hijo.GetValuePattern()
                if vp:
                    return vp.Value
            except:
                pass

            try:
                return hijo.Name
            except:
                pass

    return ""


def seleccionar_farmacia_por_codigo(codigo_objetivo: str):
    from time import sleep

    import uiautomation as auto

    codigo_objetivo = normalizar(codigo_objetivo)

    # 🔹 Abrir ventana
    auto.Click(440, 115)
    sleep(0.5)
    auto.SendKeys("{Enter}")
    sleep(0.7)

    ventana = auto.WindowControl(Name="Selección de Farmacias")

    if not ventana.Exists(3):
        raise Exception("No se encontró la ventana")

    ventana.SetActive()
    sleep(0.5)

    filas = []

    # 🔥 obtener filas ("1","2","3"...)
    for control, _ in auto.WalkControl(ventana):
        if control.ControlTypeName == "CustomControl" and control.Name.isdigit():
            filas.append(control)

    filas.sort(key=lambda x: int(x.Name))

    if not filas:
        raise Exception("No se encontraron filas")

    # 🔍 buscar por código dentro del EditControl
    for fila in filas:
        try:
            celdas = fila.GetChildren()

            if len(celdas) >= 2:
                celda_codigo = celdas[1]

                texto = obtener_texto_edit(celda_codigo)
                texto = normalizar(texto)

                # DEBUG
                # print("Código leído:", texto)

                if codigo_objetivo == texto:
                    fila.Click()
                    sleep(0.2)
                    auto.SendKeys("{Enter}")
                    return

        except:
            continue

    raise Exception(f"No se encontró farmacia con código: {codigo_objetivo}")


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
    print("Navegando al módulo de Registro de Pedido...")

    panel_window = PaneControl(foundIndex=1, searchDepth=5)
    panel_window.SetFocus()

    # 🔹 Selecionar farmacia por su nombre
    # seleccionar_farmacia("HOSP. CENTRAL")
    seleccionar_farmacia_por_codigo("06732F02")
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

    # 🔹 Forma de pago en la forma antigua como lo haciamos antes sin logica y ingresando el dato nosotros mismos (posición 9: sis)
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
        Producto(nombre="ACIDO ACETILSALICILICO - 500 mg - TABLET -", cantidad=3),
        Producto(nombre="ACIDO ACETILSALICILICO - 100 mg - TABLET -", cantidad=7),
        Producto(nombre="ACIDO TRANEXAMICO - 250 mg - TABLET -", cantidad=6),
        Producto(nombre="ACIDO TRANEXAMICO - 1 g - INYECT - 10 mL", cantidad=4),
    )
    main(productos)
    # # GrdDeta is the other table

    """
        Producto(nombre="ACIDO ACETILSALICILICO - 500 mg - TABLET -", cantidad=3),
        Producto(nombre="ACIDO ACETILSALICILICO - 100 mg - TABLET -", cantidad=7),
        Producto(nombre="ACIDO TRANEXAMICO - 250 mg - TABLET -", cantidad=6),
        Producto(nombre="ACIDO TRANEXAMICO - 1 g - INYECT - 10 mL", cantidad=4),
        Producto(nombre="ALCOHOL ETILICO (ETANOL) - 96 % - SOLUCI - 1 L", cantidad=5),
    """
