from datetime import datetime
from os import environ
from subprocess import Popen
from time import sleep

import uiautomation as auto
from dotenv import load_dotenv
from uiautomation import PaneControl, WindowControl

from src.models.ingreso import Ingreso
from src.models.producto_ingreso import ProductoIngreso
from src.sidmed._login import login

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


def seleccionar_combo_por_texto(nombre_combo: str, texto_objetivo: str):
    combo = auto.ComboBoxControl(Name=nombre_combo)

    if not combo.Exists():
        raise Exception(f"No se encontró combo: {nombre_combo}")

    combo.Click()
    for i in range(10):  # NOTE: Generic way to go up, not necesarily eficient.
        auto.SendKeys("{UP}")
    children = combo.GetChildren()
    elementos = [child.Name.strip() for child in children]
    for child in children:
        if child.Name.strip() == texto_objetivo:
            child.Click()
            return

    raise Exception(f"No se encontró el texto: {texto_objetivo}")


def seleccionar_combo_por_texto_con_autoenter(nombre_combo: str, texto_objetivo: str):
    """Aqui, si pones Up o DOWN se selecciona la opcion, tener cuidado."""
    combo = auto.ComboBoxControl(Name=nombre_combo)

    if not combo.Exists():
        raise Exception(f"No se encontró combo: {nombre_combo}")

    combo.Click()
    children = combo.GetChildren()
    elementos = [child.Name.strip() for child in children]
    for child in children:
        if child.Name.strip() == texto_objetivo:
            child.Click()
            return

    raise Exception(f"No se encontró el texto: {texto_objetivo}")


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

    sleep(0.3)
    auto.Click(780, 250)
    sleep(0.3)
    auto.Click(580, 360)
    auto.SendKeys("{Enter}")

    seleccionar_combo_por_texto_con_autoenter("cmbConcepto", ingreso.concepto)

    codigo = generar_codigo_ngr()
    registro.EditControl(Name="txtGuiaRemision").SendKeys(codigo)

    registro.ButtonControl(Name="...", foundIndex=5).Click()
    auto.SendKeys("{Enter}")

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
    for ingreso in ingresos:
        procesar_ingreso(ingreso)
    return None


def guardar():
    CmdSave = auto.ButtonControl(Name="CmdSave")
    CmdSave.Click()
    sleep(0.3)


def procesar_ingreso(ingreso: Ingreso):

    login(username, password)
    navegar_a_ingresos()
    abrir_registro()
    registro = abrir_registro()
    rellenar_cabecera(registro, ingreso)
    agregar_productos(registro, ingreso)
    guardar()
    sleep(0.3)
