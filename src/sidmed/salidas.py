from random import randint
from subprocess import Popen
from time import sleep

from src.helpers.manejo_errores import cerrar_ventana_segura
from src.reportes.excel_writer import guardar_movimientos
from ..logger import logger


from uiautomation import (
    ListItemControl,
    DocumentControl,
    EditControl,
    WindowControl,
    TableControl,
    ComboBoxControl,
    CustomControl,
    DataItemControl,
    SendKeys,
    Click,
    ButtonControl,
)


from src.models.producto_ingreso import ProductoIngreso
from src.models.Salidas import Salidas
from src.sidmed.ingreso import (
    cerrar_sismed,
    guardar,
    seleccionar_combo_por_texto,
    seleccionar_combo_por_texto_con_autoenter,
    extraer_correlativo_almacen,
)

from ..sidmed._login import login
from src.reportes.excel_schema import crear_row_salida
from src.reportes.excel_writer import (
    guardar_movimientos,
    obtener_siguiente_numero_procesado,
)

from ..config import SISMED_PASSWORD, SISMED_USERNAME, SISMED_EXE

# =========================================================
# 🔹 HELPERS
# =========================================================


def seleccionar_combo_sismed(nombre_combo: str, texto_objetivo: str, max_intentos=20):
    combo: ComboBoxControl = ComboBoxControl(Name=nombre_combo)

    if not combo.Exists():
        raise Exception(f"No se encontró combo: {nombre_combo}")

    combo.Click()
    sleep(0.5)

    # Baja hasta encontrar el texto
    for i in range(max_intentos):
        # intenta seleccionar visible
        item: ListItemControl = ListItemControl(RegexName=texto_objetivo)

        if item.Exists(1):
            item.Click()
            logger.info(f"✅ Encontrado: {texto_objetivo}")
            return

        SendKeys("{DOWN}")
        sleep(0.2)

    raise Exception(f"❌ No se encontró el concepto: {texto_objetivo}")


# =========================================================
# 🔹 FLUJO BASE
# =========================================================


def Login() -> None:
    """No used, may be a scheme for a future refactor."""
    Popen(SISMED_EXE)

    login_window = WindowControl(Name="Acceso al Sistema")

    if login_window.Exists(10):
        login_window.EditControl(Name="txtUsuario").SendKeys(SISMED_USERNAME)
        login_window.EditControl(Name="txtClave").SendKeys(SISMED_PASSWORD)

        login_window.ButtonControl(Name="Aceptar").Click()
        logger.info("✅ Login realizado")
    else:
        raise Exception("❌ No se encontró la ventana de login")

    sleep(1)

    # 🔹 cerrar ventana de vencidos
    ventana_vencidos = WindowControl(Name="Productos Vencidos y por Vencer")

    if ventana_vencidos.Exists(5):
        ventana_vencidos.ButtonControl(Name="Salir").Click()
        logger.info("🧹 Ventana de productos vencidos cerrada")
    return None


def Navegar_Salidas() -> WindowControl:
    Click(355, 115)
    sleep(0.3)
    SendKeys("{Enter}")

    sleep(0.3)
    Click(48, 122)

    sleep(0.3)
    Click(455, 115)
    SendKeys("{Enter}")

    registro = WindowControl(Name="Registro de Salidas ")

    for intento in range(3):
        if registro.Exists(5):
            logger.info("✅ Ventana encontrada")
            sleep(0.3)
            registro.ButtonControl(Name="CmdNew").Click()
            return registro
        else:
            logger.info(f"⚠️ Intento {intento+1}: No se encontró la ventana")
            sleep(1)

    raise Exception("❌ No se encontró la ventana 'Registro de Salidas'")


# =========================================================
# 🔹 CABECERA
# =========================================================


def debug_tabla_almacenes():
    tabla: TableControl = TableControl(Name="GrdCatalogo")

    if not tabla.Exists(5):
        raise Exception("❌ No se encontró la tabla de almacenes")

    logger.info("🔍 ===== INICIO DEBUG TABLA =====")

    filas = tabla.GetChildren()

    for i, fila in enumerate(filas):
        logger.info(f"\n🧾 FILA {i} → {fila.ControlTypeName}")

        grupos = fila.GetChildren()

        for j, grupo in enumerate(grupos):
            logger.info(f"   📦 GRUPO {j} → {grupo.ControlTypeName}")

            celdas = grupo.GetChildren()

            for k, celda in enumerate(celdas):
                texto = celda.Name.strip()
                logger.info(f"      🔹 Col {k}: '{texto}'")

    logger.info("\n🔍 ===== FIN DEBUG TABLA =====")


def seleccionar_almacen_destino_por_codigo(codigo_objetivo: str):
    codigo_objetivo = str(codigo_objetivo).strip()

    tabla_padre: TableControl = TableControl(Name="GrdCatalogo")
    tabla = tabla_padre.TableControl(Name="View 1")

    children = tabla.GetChildren()
    header = children[0]
    filas: list[CustomControl] = children[1:]
    # Lookin for code

    for fila in filas:
        code_data_item: DataItemControl = fila.DataItemControl(
            searchDepth=1, foundIndex=2, Name=""
        )
        xd = code_data_item.GetChildren()
        xdd = xd[0].GetChildren()
        text_edit: EditControl = code_data_item.EditControl(searchDepth=1, Name="Text1")
        codigo = text_edit.GetValuePattern().Value

        if codigo.strip() == codigo_objetivo:

            code_data_item.Click()  # más preciso
            return None

    raise Exception(f"❌ No se encontró el código: {codigo_objetivo}")


def rellenar_cabecera_salidas(registro: WindowControl, salidas: Salidas):

    sleep(1)
    # 🔹 Almacén origen (código)
    Click(780, 230)
    SendKeys(salidas.almacen_origen)
    SendKeys("{Enter}")

    sleep(0.3)

    # 🔹 Almacén destino (nombre)
    Click(1140, 230)
    sleep(2)  # 🔥 importante que cargue la tabla
    seleccionar_almacen_destino_por_codigo(salidas.almacen_destino)
    ButtonControl(Name="Aceptar").Click()
    sleep(0.3)

    # 🔹 Almacen virtual
    Click(780, 250)
    sleep(1)  # 🔥 espera que abra la ventana

    SendKeys(salidas.almacen_virtual_origen)
    sleep(1)

    # 🔥 buscar

    SendKeys("{Enter}")

    # 🔹 Concepto (combo)
    # seleccionar_combo_por_texto("cmbConcepto", salidas.concepto)
    # NOTE: Se tomo la decision de Harcodear ya que almenos se tiene entendido que siempre sera distribucion, ademas de que esta muy dificil poder selecionar la acion ya que si jugamos con las opciones algunas quitan el almacen destino y a volver a querer poner distribucion nos da error
    Click(700, 280)
    sleep(0.3)
    Click(704, 340)
    sleep(0.3)
    Click(507, 307)
    sleep(0.3)

    registro.EditControl(Name="txtReferencia").SendKeys(salidas.referencia)


def procesar_salidas(salidas: tuple[Salidas, ...]) -> None:
    k_salud_correlativo = randint(1_000_000, 9_999_999)
    rows: list[dict] = []

    numero_procesado = obtener_siguiente_numero_procesado()

    for salida in salidas:

        try:
            correlativo = procesar_salida(salida)

            row = crear_row_salida(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=k_salud_correlativo,
                correlativo_sismed=correlativo,
                salida=salida,
                estado="OK",
            )

        except Exception as e:
            logger.exception("Error procesando una salida.")

            row = crear_row_salida(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=k_salud_correlativo,
                correlativo_sismed="",
                salida=salida,
                estado="ERROR",
                error=str(e),
            )

        rows.append(row)

        k_salud_correlativo += 1
        numero_procesado += 1

    guardar_movimientos(rows)

    sleep(5)


def agregar_producto(producto: ProductoIngreso):

    # se iba a trabajar usando inspecto pero la ventana cambia de nombre segun el almacen virtual seleccionado, alm destino, almacen origen, etc, por lo que es muy dificil asegurar el nombre de la ventana, por lo que se decidio trabajar con clicks en coordenadas especificas, ya que se tiene entendido que la ventana siempre va a tener la misma estructura y los mismos campos en las mismas posiciones

    SendKeys("{CONTROL}{INSERT}")  # abre ventana de agregar producto
    sleep(1)
    Click(825, 355)  # clic en el campo de codigo
    sleep(0.3)
    Click(615, 315)  # clic en el txt busca
    sleep(0.3)
    SendKeys(producto.codigo)  # busca el producto
    sleep(0.3)
    SendKeys("{Enter}")
    sleep(0.3)
    SendKeys("{Enter}")  # selecciona el producto
    sleep(0.3)
    SendKeys("{Enter}")
    sleep(0.3)
    SendKeys(str(producto.cantidad))  # ingresa la cantidad
    sleep(0.3)
    SendKeys("{Enter}")
    SendKeys("{Enter}")
    pass


def procesar_salida(salidas: Salidas) -> str:

    login(SISMED_USERNAME, SISMED_PASSWORD)
    registro: WindowControl = Navegar_Salidas()
    rellenar_cabecera_salidas(registro, salidas)
    for producto in salidas.productos:
        agregar_producto(producto)
    guardar()
    # 🔹 Esperamos un momento a que Sismed procese y salga el aviso
    sleep(1)
    # 🔹 Capturamos el correlativo
    correlativo: str = extraer_correlativo_almacen()

    cerrar_sismed()
    sleep(5)

    return correlativo
