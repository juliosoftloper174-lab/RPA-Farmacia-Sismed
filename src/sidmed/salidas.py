from datetime import datetime
from os import environ
from subprocess import Popen
from time import sleep

import uiautomation as auto
from dotenv import load_dotenv
from uiautomation import EditControl, WindowControl
from uiautomation import CustomControl, DataItemControl
from polars import DataFrame
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


def debug_tabla_almacenes():
    tabla = auto.TableControl(Name="GrdCatalogo")

    if not tabla.Exists(5):
        raise Exception("❌ No se encontró la tabla de almacenes")

    print("🔍 ===== INICIO DEBUG TABLA =====")

    filas = tabla.GetChildren()

    for i, fila in enumerate(filas):
        print(f"\n🧾 FILA {i} → {fila.ControlTypeName}")

        grupos = fila.GetChildren()

        for j, grupo in enumerate(grupos):
            print(f"   📦 GRUPO {j} → {grupo.ControlTypeName}")

            celdas = grupo.GetChildren()

            for k, celda in enumerate(celdas):
                texto = celda.Name.strip()
                print(f"      🔹 Col {k}: '{texto}'")

    print("\n🔍 ===== FIN DEBUG TABLA =====")


def seleccionar_almacen_destino_por_codigo(codigo_objetivo: str):
    codigo_objetivo = str(codigo_objetivo).strip()

    tabla_padre = auto.TableControl(Name="GrdCatalogo")
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
        text_edit = code_data_item.EditControl(searchDepth=1, Name="Text1")
        codigo = text_edit.GetValuePattern().Value

        if codigo.strip() == codigo_objetivo:

            code_data_item.Click()  # más preciso
            return None

    raise Exception(f"❌ No se encontró el código: {codigo_objetivo}")


def rellenar_cabecera_salidas(registro: WindowControl, salidas: Salidas):

    sleep(1)
    # 🔹 Almacén origen (código)
    auto.Click(780, 230)
    auto.SendKeys(salidas.almacen_origen)
    auto.SendKeys("{Enter}")

    sleep(0.3)

    # 🔹 Almacén destino (nombre)
    auto.Click(1140, 230)
    sleep(2)  # 🔥 importante que cargue la tabla
    seleccionar_almacen_destino_por_codigo(salidas.almacen_destino)
    auto.ButtonControl(Name="Aceptar").Click()
    sleep(0.3)

    # 🔹 Almacen virtual
    auto.Click(780, 250)
    sleep(1)  # 🔥 espera que abra la ventana

    auto.SendKeys(salidas.almacen_virtual_origen)
    sleep(1)

    # 🔥 buscar

    auto.SendKeys("{Enter}")

    # 🔹 Concepto (combo)
    # seleccionar_combo_por_texto("cmbConcepto", salidas.concepto)
    # NOTE: Se tomo la decision de Harcodear ya que almenos se tiene entendido que siempre sera distribucion, ademas de que esta muy dificil poder selecionar la acion ya que si jugamos con las opciones algunas quitan el almacen destino y a volver a querer poner distribucion nos da error
    auto.Click(700, 280)
    sleep(0.3)
    auto.Click(704, 340)
    sleep(0.3)
    auto.Click(507, 307)
    sleep(0.3)

    registro.EditControl(Name="txtReferencia").SendKeys(salidas.referencia)


def procesar_salidas(salidas: tuple[Salidas, ...]) -> None:

    rows: list[dict] = []

    for i, salida in enumerate(salidas, 1):

        try:
            correlativo = procesar_salida(salida)

            now = datetime.now()

            row = {
                "N° Procesado": i,
                "Fecha": now.strftime("%Y-%m-%d"),
                "Hora": now.strftime("%H:%M:%S"),
                "Usuario": username,
                "TipoMovimiento": "SALIDA",
                "Estado": "OK",
                "Error": "",
                "CorrelativoSismed": correlativo,
                "AlmacenOrigen": salida.almacen_origen,
                "AlmacenDestino": salida.almacen_destino,
                "AlmacenVirtual": salida.almacen_virtual_origen,
                "Concepto": salida.concepto,
                "Referencia": salida.referencia,
                "CantidadProductos": len(salida.productos),
            }

        except Exception as e:

            row = {
                "N° Procesado": i,
                "Fecha": "",
                "Hora": "",
                "Usuario": username,
                "TipoMovimiento": "SALIDA",
                "Estado": "ERROR",
                "Error": str(e),
                "CorrelativoSismed": "",
                "AlmacenOrigen": salida.almacen_origen,
                "AlmacenDestino": salida.almacen_destino,
                "AlmacenVirtual": salida.almacen_virtual_origen,
                "Concepto": salida.concepto,
                "Referencia": salida.referencia,
                "CantidadProductos": len(salida.productos),
            }

        rows.append(row)

    df = DataFrame(rows)

    df.write_excel("salidas.xlsx")

    sleep(5)


def agregar_producto(producto: ProductoIngreso):

    # se iba a trabajar usando inspecto pero la ventana cambia de nombre segun el almacen virtual seleccionado, alm destino, almacen origen, etc, por lo que es muy dificil asegurar el nombre de la ventana, por lo que se decidio trabajar con clicks en coordenadas especificas, ya que se tiene entendido que la ventana siempre va a tener la misma estructura y los mismos campos en las mismas posiciones

    auto.SendKeys("{CONTROL}{INSERT}")  # abre ventana de agregar producto
    sleep(1)
    auto.Click(825, 355)  # clic en el campo de codigo
    sleep(0.3)
    auto.Click(615, 315)  # clic en el txt busca
    sleep(0.3)
    auto.SendKeys(producto.codigo)  # busca el producto
    sleep(0.3)
    auto.SendKeys("{Enter}")
    sleep(0.3)
    auto.SendKeys("{Enter}")  # selecciona el producto
    sleep(0.3)
    auto.SendKeys("{Enter}")
    sleep(0.3)
    auto.SendKeys(str(producto.cantidad))  # ingresa la cantidad
    sleep(0.3)
    auto.SendKeys("{Enter}")
    auto.SendKeys("{Enter}")
    pass


def procesar_salida(salidas: Salidas) -> str:

    login(username, password)
    registro = Navegar_Salidas()
    rellenar_cabecera_salidas(registro, salidas)
    for producto in salidas.productos:
        agregar_producto(producto)
    guardar()

    # 🔹 Esperamos un momento a que Sismed procese y salga el aviso
    sleep(2)

    # 🔹 Capturamos el correlativo
    correlativo: str = extraer_correlativo_almacen()

    sleep(5)

    cerrar_sismed()
    sleep(5)
    sleep(5)
    return correlativo
