from datetime import datetime
from os import environ
from subprocess import Popen
from time import sleep

import uiautomation as auto
from dotenv import load_dotenv
from uiautomation import WindowControl

from src.models.producto_ingreso import ProductoIngreso
from src.models.Salidas import Salidas

from ..sidmed._login import login

# =========================================================
# 🔹 CONFIG
# =========================================================
load_dotenv()
SISMED_EXE: str = environ["SISMED_EXE"]
username: str = environ["SISMED_USERNAME"]
password: str = environ["SISMED_PASSWORD"]
# =========================================================
# 🔹 HELPERS
# =========================================================


def seleccionar_combo_sismed(nombre_combo: str, texto_objetivo: str, max_intentos=20):
    combo = auto.ComboBoxControl(Name=nombre_combo)

    if not combo.Exists():
        raise Exception(f"No se encontró combo: {nombre_combo}")

    combo.Click()
    sleep(0.5)

    # Baja hasta encontrar el texto
    for i in range(max_intentos):
        # intenta seleccionar visible
        item = auto.ListItemControl(RegexName=texto_objetivo)

        if item.Exists(1):
            item.Click()
            print(f"✅ Encontrado: {texto_objetivo}")
            return

        auto.SendKeys("{DOWN}")
        sleep(0.2)

    raise Exception(f"❌ No se encontró el concepto: {texto_objetivo}")


def seleccionar_almacen_destino_por_codigo(codigo_objetivo: str):
    tabla = auto.TableControl(Name="GrdCatalogo")

    if not tabla.Exists(5):
        raise Exception("❌ No se encontró la tabla de almacenes")

    filas = tabla.GetChildren()

    for fila in filas:
        texto = fila.Name  # 🔥 aquí viene todo el contenido de la fila

        if codigo_objetivo in texto:
            fila.Click()
            print(f"✅ Seleccionado: {codigo_objetivo}")
            return

    raise Exception(f"❌ No se encontró el código: {codigo_objetivo}")


# =========================================================
# 🔹 FLUJO BASE
# =========================================================


def Login() -> None:
    Popen(SISMED_EXE)

    login_window = WindowControl(Name="Acceso al Sistema")

    if login_window.Exists(10):
        login_window.EditControl(Name="txtUsuario").SendKeys(environ["SISMED_USERNAME"])
        login_window.EditControl(Name="txtClave").SendKeys(
            environ["SIDMED_PASSWORD"]  # ✅ corregido
        )

        login_window.ButtonControl(Name="Aceptar").Click()
        print("✅ Login realizado")
    else:
        raise Exception("❌ No se encontró la ventana de login")

    sleep(1)

    # 🔹 cerrar ventana de vencidos
    ventana_vencidos = WindowControl(Name="Productos Vencidos y por Vencer")

    if ventana_vencidos.Exists(5):
        ventana_vencidos.ButtonControl(Name="Salir").Click()
        print("🧹 Ventana de productos vencidos cerrada")


def Navegar_Salidas() -> WindowControl:
    auto.Click(355, 115)
    sleep(0.3)
    auto.SendKeys("{Enter}")

    sleep(0.3)
    auto.Click(48, 122)

    sleep(0.3)
    auto.Click(455, 115)
    auto.SendKeys("{Enter}")

    registro = WindowControl(Name="Registro de Salidas ")

    for intento in range(3):
        if registro.Exists(5):
            print("✅ Ventana encontrada")
            sleep(0.3)
            registro.ButtonControl(Name="CmdNew").Click()
            return registro
        else:
            print(f"⚠️ Intento {intento+1}: No se encontró la ventana")
            sleep(1)

    raise Exception("❌ No se encontró la ventana 'Registro de Salidas'")


# =========================================================
# 🔹 CABECERA
# =========================================================


def rellenar_cabecera_salidas(registro: WindowControl, salidas: Salidas):

    sleep(1)
    # 🔹 Almacén origen (código)
    auto.Click(780, 230)
    auto.SendKeys(salidas.almacen_origen)
    auto.SendKeys("{Enter}")

    sleep(0.3)

    # 🔹 Almacén destino (nombre)
    # auto.Click(1140, 230)
    # seleccionar_almacen_destino_por_codigo("06732F04")
    # auto.ButtonControl(Name="Aceptar").Click()

    sleep(0.3)

    # 🔹 Alamcen virtual
    auto.Click(780, 250)
    sleep(0.3)
    auto.Click(580, 360)
    auto.SendKeys("{Enter}")

    # 🔹 Concepto (combo)
    seleccionar_combo_sismed("cmbConcepto", salidas.concepto)

    # 🔹 Referencia
    registro.EditControl(Name="txtReferencia").SendKeys(salidas.referencia)


# =========================================================
# 🔹 MAIN
# =========================================================


def procesar_salidas(salidas: tuple[Salidas, ...]) -> None:
    for salida in salidas:
        procesar_salida(salida)
    return None


def procesar_salida(salidas: Salidas):

    login(username, password)
    registro = Navegar_Salidas()

    rellenar_cabecera_salidas(registro, salidas)

    sleep(0.5)
