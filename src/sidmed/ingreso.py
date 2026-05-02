from datetime import datetime
from os import environ
from subprocess import Popen
from time import sleep

import uiautomation as auto
from dotenv import load_dotenv
from uiautomation import PaneControl, WindowControl

from src.models.ingreso import Ingreso
from src.models.producto_ingreso import ProductoIngreso

# =========================================================
# 🔹 CONFIG
# =========================================================
load_dotenv()
SISMED_EXE: str = environ["SISMED_EXE"]

# =========================================================
# 🔹 HELPERS
# =========================================================


def generar_codigo_ngr() -> str:
    return datetime.now().strftime("%Y%m%d%H%M")


def seleccionar_combo_por_indice(nombre_combo: str, indice: int):
    combo = auto.ComboBoxControl(Name=nombre_combo)

    if not combo.Exists():
        raise Exception(f"No se encontró combo: {nombre_combo}")

    combo.Click()
    sleep(0.3)

    for _ in range(indice):
        auto.SendKeys("{DOWN}")
        sleep(0.1)

    auto.SendKeys("{ENTER}")


# =========================================================
# 🔹 FLUJO BASE
# =========================================================


def login():
    Popen(SISMED_EXE)

    login_window = WindowControl(Name="Acceso al Sistema")
    login_window.Exists(10)

    login_window.EditControl(Name="txtUsuario").SendKeys(environ["SISMED_USERNAME"])
    login_window.EditControl(Name="txtClave").SendKeys(environ["SIDMED_PASSWORD"])

    login_window.ButtonControl(Name="Aceptar").Click()


def cerrar_ventana_inicial():
    ventana = WindowControl(Name="Productos Vencidos y por Vencer")

    if ventana.Exists():
        ventana.ButtonControl(Name="Salir").Click()


def navegar_a_ingresos():
    panel = PaneControl(foundIndex=1)
    panel.SetFocus()

    auto.Click(355, 115)
    sleep(0.3)
    auto.SendKeys("{Enter}")

    sleep(0.3)
    auto.Click(48, 122)

    sleep(0.3)
    auto.Click(355, 115)
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

    combo = auto.ComboBoxControl(Name="cmbConcepto")
    combo.Click()
    auto.ListItemControl(RegexName=ingreso.concepto).Click()

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
    seleccionar_combo_por_indice("cbotipsum", producto.tipo_sum)
    seleccionar_combo_por_indice("cboffin", producto.fuente_fin)

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


def procesar_ingreso(ingreso: Ingreso):

    login()

    registro = abrir_registro()

    rellenar_cabecera(registro, ingreso)
    agregar_productos(registro, ingreso)

    sleep(0.3)
