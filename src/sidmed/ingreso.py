from datetime import datetime
from comtypes import COMError
from re import Pattern, compile
from time import sleep
from retry import retry
from uiautomation import (
    ButtonControl,
    Click,
    DocumentControl,
    SendKeys,
    SendKeys,
    TitleBarControl,
)

from src.helpers.manejo_errores import cerrar_ventana_segura
from ..helpers.selecionar import seleccionar_combo_por_texto
from ..helpers.selecionar import seleccionar_combo_por_texto_con_autoenter
from ..config import SISMED_PASSWORD, SISMED_USERNAME

from uiautomation import WindowControl
from src.models.ingreso import Ingreso
from src.models.Medicamento import Medicamento
from src.sidmed._login import login
from ..helpers.windows import *
from random import randint
from src.logger import logger
from src.reportes.excel_schema import crear_row_ingreso
from src.reportes.excel_writer import (
    guardar_movimientos,
    obtener_siguiente_numero_procesado,
)

# =========================================================
# 🔹 HELPERS
# =========================================================


def generar_codigo_ngr() -> str:
    return datetime.now().strftime("%Y%m%d%H%M")


# =========================================================
# 🔹 FLUJO BASE
# =========================================================


def navegar_a_ingresos():
    SendKeys("{Enter}")
    sleep(1)
    # quiero mandarle hacia abajo para que se posicione en ingresos
    SendKeys("{DOWN}")
    sleep(1)
    SendKeys("{DOWN}")
    sleep(1)
    SendKeys("{ENTER}")
    sleep(1)
    Click(360, 100)
    sleep(1)
    SendKeys("{Enter}")


def abrir_registro() -> WindowControl:

    registro = WindowControl(Name="Registro de Ingresos .")
    registro.Exists(10)

    registro.ButtonControl(Name="CmdNew").Click()
    return registro


def rellenar_ups(codigo_ups: str) -> None:
    # Abrir modal UPS (click ciego)
    sleep(1)
    Click(750, 380)
    sleep(1)

    # Escribir código
    # SendKeys(codigo_ups)
    SendKeys(
        "000"
    )  # NOTE: por ahora se asume que siempre se ingresa el ups 000 que significa sin ups
    sleep(1)

    # Botón aceptar
    # registro_pedido_window: WindowControl = FARMACIA_PANEL.WindowControl(searchDepth=1, Name="Registro de Pedido")
    # aceptar: ButtonControl = registro_pedido_window.ButtonControl(Name="Aceptar")
    aceptar: ButtonControl = ButtonControl(Name="Aceptar")
    aceptar.Click()


# =========================================================
# 🔹 CABECERA
# =========================================================


def rellenar_cabecera(registro: WindowControl, ingreso: Ingreso):

    Click(700, 230)
    sleep(1.8)
    # SendKeys(ingreso.almacen_origen)
    SendKeys("ALM. ANEXO RIOJA - SAN MARTIN")
    sleep(1.8)
    SendKeys("{Enter}{Enter}")

    sleep(0.5)
    Click(1140, 230)
    SendKeys(ingreso.almacen_destino)
    sleep(0.5)
    SendKeys("{Enter}")
    # NOTE: aqui se rellena el almacen virtual, esto no lee la base de datos, se asume que siempre sera el primero, se puede mejorar este apartado, por ahora trabajemoslo asi
    sleep(1.8)
    Click(775, 255)
    sleep(1.8)
    SendKeys(ingreso.almacen_virtual_origen)
    sleep(1.8)
    SendKeys("{Enter}")
    sleep(1.5)

    seleccionar_combo_por_texto_con_autoenter("cmbConcepto", ingreso.concepto)

    codigo = generar_codigo_ngr()
    registro.EditControl(Name="txtGuiaRemision").SendKeys(codigo)

    rellenar_ups("000")


# =========================================================
# 🔹 PRODUCTOS
# =========================================================


def abrir_modal():

    sleep(0.5)
    SendKeys("{CONTROL}{INSERT}")
    sleep(5)


def limpiar_y_escribir(edit, valor):

    # foco real
    edit.Click()
    sleep(0.5)

    # seleccionar todo
    SendKeys("{CONTROL}a")
    sleep(0.3)

    # borrar
    SendKeys("{DEL}")
    sleep(0.3)

    # escribir nuevo valor
    edit.SendKeys(str(valor))
    sleep(0.5)


def limpiar_registro_sanitario(edit, valor):

    edit.Click()
    sleep(0.5)

    # borrar contenido actual
    for _ in range(13):
        SendKeys("{BS}")
        sleep(0.05)

    sleep(0.3)

    # escribir nuevo valor
    edit.SendKeys(str(valor))
    sleep(0.5)


def formatear_fecha_sismed(fecha: str) -> str:
    """
    Convierte:
    2029/12/07

    a:
    07122029
    """

    anio, mes, dia = fecha.split("/")

    return f"{dia}{mes}{anio}"


def agregar_producto(registro: WindowControl, producto: Medicamento):

    # =====================================================
    # CODIGO
    # =====================================================

    registro.EditControl(Name="txtCodigo").SendKeys(producto.codigo)

    SendKeys("{Enter}")
    sleep(0.5)

    # =====================================================
    # LOTE
    # =====================================================

    registro.EditControl(Name="txtLote").SendKeys(producto.lote)

    SendKeys("{Enter}")
    sleep(1)

    # =====================================================
    # FECHA
    # =====================================================

    fecha_vencimiento_formato = formatear_fecha_sismed(producto.fecha_vencimiento)

    # seleccionar checkpoint del día
    Click(810, 632)
    # registro.CheckBoxControl(Name="txtdia").Click()

    sleep(0.5)

    # escribir fecha completa:
    # DDMMYYYY
    SendKeys(fecha_vencimiento_formato)

    sleep(0.5)

    # =====================================================
    # REGISTRO SANITARIO
    # =====================================================

    # el contenido ya queda seleccionado automáticamente
    # pero por seguridad escribimos primero una letra
    SendKeys("a")

    sleep(0.5)

    # eliminamos todo el contenido seleccionado
    SendKeys("{BACK}")

    sleep(0.3)

    # escribimos el registro sanitario real
    registro.EditControl(Name="txtFabricante").SendKeys(producto.registro_sanitario)

    sleep(0.5)

    SendKeys("{Enter}")

    sleep(0.5)

    # =====================================================
    # TIPO DE SUMINISTRO
    # =====================================================

    seleccionar_combo_por_texto("cbotipsum", producto.tipo_sum)

    # =====================================================
    # FUENTE DE FINANCIAMIENTO
    # =====================================================

    seleccionar_combo_por_texto("cboffin", producto.fuente_fin)

    # =====================================================
    # CANTIDAD
    # =====================================================

    registro.EditControl(Name="txtCantidad").SendKeys(str(producto.cantidad))

    SendKeys("{Enter}")

    sleep(0.5)

    # =====================================================
    # TEMPERATURA
    # =====================================================

    # dejamos el valor por defecto
    SendKeys("{Enter}")

    sleep(0.5)

    # =====================================================
    # PRECIO
    # =====================================================

    registro.EditControl(Name="txtPrecio").SendKeys(str(producto.precio_compra))

    SendKeys("{Enter}")

    sleep(0.5)

    # =====================================================
    # ACEPTAR
    # =====================================================

    registro.ButtonControl(Name="cmdAceptar").Click()

    sleep(1)


def agregar_productos(registro: WindowControl, ingreso: Ingreso):
    for producto in ingreso.medicamentos:
        abrir_modal()
        agregar_producto(registro, producto)


# =========================================================
# 🔹 MAIN
# =========================================================


def procesar_ingresos(ingresos: tuple[Ingreso, ...]) -> None:
    k_salud_correlativo = randint(1_000_000, 9_999_999)
    rows: list[dict] = []

    numero_procesado = obtener_siguiente_numero_procesado()

    for ingreso in ingresos:

        try:
            correlativo = procesar_ingreso(ingreso)

            row = crear_row_ingreso(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=k_salud_correlativo,
                correlativo_sismed=correlativo,
                ingreso=ingreso,
                estado="OK",
            )

        except Exception as e:
            logger.exception("Error procesando un ingreso.")

            row = crear_row_ingreso(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=k_salud_correlativo,
                correlativo_sismed="",
                ingreso=ingreso,
                estado="ERROR",
                error=str(e),
            )

        rows.append(row)

        k_salud_correlativo += 1
        numero_procesado += 1

    guardar_movimientos(rows)

    sleep(2)


def guardar() -> None:
    CmdSave: ButtonControl = ButtonControl(Name="CmdSave")
    CmdSave.Click()
    sleep(0.5)
    return None


VENTANA_ERROR = WindowControl(Name="Program Error")
BOTON_IGNORAR_ERROR = VENTANA_ERROR.ButtonControl(Name="Ignore")
# I just want the digits after the N°
CORRELATIVO_PATTERN: Pattern = compile(
    r"Se grabó correctamente la Nota de (Ingreso|Salida) N° (\d+)"
)


@retry(tries=3, backoff=2, delay=2, exceptions=(COMError,))
def close_doc_windows() -> None:
    """

    # NOTE: Retry because some random errors happen related to COMS. Idk how to avoid them.

    # TODO: Close just one, close_doc_button or ignore_button.
    # Both cannot exist at the same time.
    """

    program_error_window: WindowControl = WindowControl(Name="Program Error")
    ignore_button: ButtonControl = program_error_window.ButtonControl(
        searchDepth=1, Name="Ignore"
    )
    if ignore_button.Exists():
        ignore_button.GetInvokePattern().Invoke()
        logger.debug("Ignored program error window.")

    doc_window: DocumentControl = DocumentControl(
        RegexName=r"^Report Designer - .*\.frx - Page 1$"
    )
    title_bar: TitleBarControl = doc_window.TitleBarControl(searchDepth=1)
    close_doc_button: ButtonControl = title_bar.ButtonControl(
        searchDepth=1, Name="Cerrar"
    )
    if close_doc_button.Exists():
        close_doc_button.GetInvokePattern().Invoke()
        logger.debug("Closed report designer window.")

    return None


def extraer_correlativo_almacen() -> str:

    ALMACEN_WINDOW: WindowControl = WindowControl(
        searchDepth=1, Name="ALMACEN - MINSA SISMED"
    )

    aviso = ALMACEN_WINDOW.WindowControl(searchDepth=1, Name="Aviso")

    if aviso.Exists():

        mensaje: str = aviso.TextControl(searchDepth=1).Name.strip()

        logger.debug(f"{mensaje = }.")

        accept_button: ButtonControl = aviso.ButtonControl(Name="Aceptar")
        accept_button.GetInvokePattern().Invoke()

        close_doc_windows()

        if correlative_match := CORRELATIVO_PATTERN.search(mensaje):
            return correlative_match.group(2)

        raise ValueError(f"SISMED: {mensaje}")

    minsa = ALMACEN_WINDOW.WindowControl(searchDepth=1, Name="MINSA SISMED")

    if minsa.Exists(1):

        mensaje_error: str = minsa.TextControl(searchDepth=1, foundIndex=1).Name.strip()

        raise ValueError(f"MINSA: {mensaje_error}")

    raise RuntimeError("No se encontró ni correlativo ni mensaje de error.")


def cerrar_sismed() -> None:
    almacen_window: WindowControl = WindowControl(
        searchDepth=1, Name="ALMACEN - MINSA SISMED"
    )
    almacen_window.GetWindowPattern().Close()
    minsa_sismed_window: WindowControl = WindowControl(
        searchDepth=1, Name="MINSA SISMED"
    )
    if not (windows_pattern := minsa_sismed_window.GetWindowPattern()):
        raise RuntimeError("No se encontró la ventana principal de Sismed.")
    windows_pattern.Close()
    return None


def procesar_ingreso(ingreso: Ingreso) -> str:
    login(SISMED_USERNAME, SISMED_PASSWORD)
    navegar_a_ingresos()

    # 🔹 Solo una vez
    registro = abrir_registro()

    rellenar_cabecera(registro, ingreso)
    agregar_productos(registro, ingreso)

    guardar()

    # 🔹 Esperamos un momento a que Sismed procese y salga el aviso
    sleep(1)

    # 🔹 Capturamos el correlativo
    correlativo: str = extraer_correlativo_almacen()

    sleep(1)

    cerrar_sismed()
    return correlativo
