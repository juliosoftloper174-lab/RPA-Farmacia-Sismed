from datetime import datetime
from os import environ

from time import sleep
from uiautomation import ButtonControl, Click, ListItemControl, SendKeys
import uiautomation as auto
from ..helpers.selecionar import seleccionar_combo_por_texto
from ..helpers.selecionar import seleccionar_combo_por_texto_con_autoenter

from dotenv import load_dotenv
from uiautomation import TextControl, WindowControl
from polars import DataFrame
from src.models.ingreso import Ingreso
from src.models.producto_ingreso import ProductoIngreso
from src.sidmed._login import login
from src.sidmed.pedido import REGISTRO_PEDIDO_WINDOW

# =========================================================
# 🔹 CONFIG
# =========================================================
load_dotenv()
SISMED_EXE: str = environ["SISMED_EXE"]

# =========================================================
# 🔹 HELPERS
# =========================================================
username: str = environ["SISMED_USERNAME"]
password: str = environ["SISMED_PASSWORD"]


def generar_codigo_ngr() -> str:
    return datetime.now().strftime("%Y%m%d%H%M")


# =========================================================
# 🔹 FLUJO BASE
# =========================================================


def navegar_a_ingresos():
    auto.SendKeys("{Enter}")
    sleep(0.3)
    # quiero mandarle hacia abajo para que se posicione en ingresos
    auto.SendKeys("{DOWN}")
    sleep(0.3)
    auto.SendKeys("{DOWN}")
    sleep(0.3)
    auto.SendKeys("{ENTER}")
    sleep(0.3)
    auto.Click(360, 100)
    sleep(0.3)
    auto.SendKeys("{Enter}")


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


# =========================================================
# 🔹 CABECERA
# =========================================================


def rellenar_cabecera(registro: WindowControl, ingreso: Ingreso):

    auto.Click(700, 230)
    auto.SendKeys(ingreso.almacen_origen)
    auto.SendKeys("{Enter}{Enter}")

    sleep(0.3)
    auto.Click(1140, 230)
    auto.SendKeys(ingreso.almacen_destino)
    auto.SendKeys("{Enter}")
    # NOTE: aqui se rellena el almacen virtual, esto no lee la base de datos, se asume que siempre sera el primero, se puede mejorar este apartado, por ahora trabajemoslo asi
    sleep(0.3)
    auto.Click(780, 250)
    sleep(0.3)
    auto.Click(580, 360)

    auto.SendKeys("{Enter}")

    seleccionar_combo_por_texto_con_autoenter("cmbConcepto", ingreso.concepto)

    codigo = generar_codigo_ngr()
    registro.EditControl(Name="txtGuiaRemision").SendKeys(codigo)

    # NOTE: aqui se rellena el UPS esto no lee la base de datos se asume que siempre sera el primero (SIN UPS), se puede mejorar este apartado, por ahora trabajemoslo asi
    # registro.ButtonControl(Name="...", foundIndex=5).Click()
    # auto.SendKeys("{Enter}")

    # prueba de rellenar ups
    sleep(0.3)
    rellenar_ups(ingreso.ups_codigo)

    registro.EditControl(Name="txtReferencia").SendKeys(ingreso.referencia)


# =========================================================
# 🔹 PRODUCTOS
# =========================================================


def abrir_modal():
    auto.Click(810, 410)
    sleep(0.3)
    auto.SendKeys("{CONTROL}{INSERT}")
    sleep(0.5)


def agregar_producto(registro: WindowControl, producto: ProductoIngreso):

    registro.EditControl(Name="txtCodigo").SendKeys(producto.codigo)
    auto.SendKeys("{Enter}")
    sleep(0.5)

    registro.EditControl(Name="txtLote").SendKeys(producto.lote)
    auto.SendKeys("{Enter}")
    sleep(0.5)

    # 🔥 combos nuevos
    seleccionar_combo_por_texto("cbotipsum", producto.tipo_sum)
    seleccionar_combo_por_texto("cboffin", producto.fuente_fin)

    registro.EditControl(Name="txtCantidad").SendKeys(str(producto.cantidad))
    auto.SendKeys("{Enter}")
    sleep(0.5)

    registro.ButtonControl(Name="cmdAceptar").Click()
    sleep(0.5)


def agregar_productos(registro: WindowControl, ingreso: Ingreso):
    for producto in ingreso.productos:
        abrir_modal()
        agregar_producto(registro, producto)


# =========================================================
# 🔹 MAIN
# =========================================================


def procesar_ingresos(ingresos: tuple[Ingreso, ...]) -> None:
    processes: list = list()
    for simulated_id, ingreso in enumerate(ingresos):
        try:
            correlativo = procesar_ingreso(ingreso)
            processes.append((simulated_id, correlativo))
        except Exception as e:
            print(f"Error al procesar el ingreso: {e}")
            processes.append((simulated_id, str(e)))
    # Save to excel

    df: DataFrame = DataFrame(processes, schema=["Ingreso", "Correlativo"])
    df.write_excel("ingresos.xlsx")

    return None


def guardar():
    CmdSave = auto.ButtonControl(Name="CmdSave")
    CmdSave.Click()
    sleep(0.3)


def test_captura_correlativo():
    resultado = extraer_correlativo_almacen()

    # Esto hará que el test falle y te muestre el valor en la cara
    assert resultado == "FORZAR_FALLO", f"El correlativo capturado fue: {resultado}"


ALMACEN_WINDOW: WindowControl = WindowControl(
    searchDepth=1, Name="ALMACEN - MINSA SISMED"
)
AVISO_DIALOG: WindowControl = ALMACEN_WINDOW.WindowControl(searchDepth=1, Name="Aviso")
CORRELATIVO_SAVED_TEXT: TextControl = AVISO_DIALOG.TextControl(
    NameRegex=r"Se grabó correctamente la Nota de (Ingreso|Salida) N° \d+"
)

MINSA_DIALOG: WindowControl = ALMACEN_WINDOW.WindowControl(
    searchDepth=1, Name="MINSA SISMED"
)
ERROR_TEXT: TextControl = MINSA_DIALOG.TextControl(searchDepth=1, foundIndex=1)


def extraer_correlativo_almacen() -> str:
    if not CORRELATIVO_SAVED_TEXT.Exists():
        raise ValueError(ERROR_TEXT.Name.strip())
    if not (text := CORRELATIVO_SAVED_TEXT.Name.strip()):
        raise ValueError("Correlativo cannot be empty.")
    correlativo: str = text.split(" ", 1)[-1].strip()
    return correlativo


def procesar_ingreso(ingreso: Ingreso) -> str:
    login(username, password)
    navegar_a_ingresos()

    # 🔹 Solo una vez
    registro = abrir_registro()

    rellenar_cabecera(registro, ingreso)
    # agregar_productos(registro, ingreso)

    guardar()

    # 🔹 Esperamos un momento a que Sismed procese y salga el aviso
    sleep(2)

    # 🔹 Capturamos el correlativo
    correlativo: str = extraer_correlativo_almacen()

    sleep(0.3)

    return correlativo
