from datetime import datetime
from os import environ
from subprocess import Popen
from time import sleep

import uiautomation as auto
from dotenv import load_dotenv
from uiautomation import PaneControl, WindowControl

# =========================================================
# 🔹 CARGA DE VARIABLES DE ENTORNO
# =========================================================
load_dotenv()

SISMED_EXE: str = environ["SISMED_EXE"]


# =========================================================
# 🔹 FUNCIONES AUXILIARES
# =========================================================


def generar_codigo_ngr() -> str:
    """
    Genera el código de N° GR basado en:
    Año + Mes + Día + Hora + Minuto
    Ejemplo: 202603111405
    """
    ahora = datetime.now()
    return ahora.strftime("%Y%m%d%H%M")


# =========================================================
# 🔹 FLUJO PRINCIPAL DEL BOT
# =========================================================


def main() -> None:

    # =====================================================
    # 1. 🔐 ABRIR SISTEMA Y HACER LOGIN
    # =====================================================
    print("Abriendo SISMED...")
    Popen(SISMED_EXE)

    login_window: WindowControl = WindowControl(searchDepth=1, Name="Acceso al Sistema")
    login_window.Exists(10)

    print("Ingresando credenciales...")

    login_window.EditControl(Name="txtUsuario").SendKeys(environ["SISMED_USERNAME"])
    login_window.EditControl(Name="txtClave").SendKeys(environ["SIDMED_PASSWORD"])

    login_window.ButtonControl(Name="Aceptar").Click()

    # =====================================================
    # 2. ❌ CERRAR VENTANA INICIAL (Productos vencidos)
    # =====================================================
    productos_window: WindowControl = WindowControl(
        searchDepth=3, Name="Productos Vencidos y por Vencer"
    )

    if productos_window.Exists():
        print("Cerrando ventana de productos...")
        productos_window.ButtonControl(Name="Salir").Click()

    # =====================================================
    # 3. 📂 NAVEGACIÓN EN EL MENÚ
    # Control de Almacenes → Procesos → Nota de Ingreso
    # =====================================================
    print("Navegando al módulo de ingresos...")

    panel_window = PaneControl(foundIndex=1, searchDepth=5)
    panel_window.SetFocus()

    auto.Click(355, 115)  # Control de Almacenes
    sleep(0.3)
    auto.SendKeys("{Enter}")

    sleep(0.3)
    auto.Click(48, 122)  # Procesos

    sleep(0.3)
    auto.Click(355, 115)  # Nota de ingreso
    auto.SendKeys("{Enter}")

    # =====================================================
    # 4. 📝 REGISTRO DE INGRESOS
    # =====================================================
    Registro = WindowControl(searchDepth=4, Name="Registro de Ingresos .")
    Registro.Exists(10)

    print("Creando nuevo registro...")
    Registro.ButtonControl(Name="CmdNew").Click()

    # =====================================================
    # 5. 🏪 SELECCIÓN DE ALMACENES
    # =====================================================

    # 🔹 Almacén Origen
    auto.Click(700, 230)
    auto.SendKeys("ALM. ANEXO RIOJA")
    auto.SendKeys("{Enter}")
    auto.SendKeys("{Enter}")

    # 🔹 Almacén Destino
    sleep(0.3)
    auto.Click(1140, 230)
    auto.SendKeys("FARM")
    auto.SendKeys("{Enter}")

    # 🔹 Almacén Virtual Origen
    sleep(0.3)
    auto.Click(780, 250)
    sleep(0.3)
    auto.Click(580, 360)
    auto.SendKeys("{Enter}")

    # =====================================================
    # 6. 📌 SELECCIÓN DE CONCEPTO
    # Siempre: DISTRIBUCIÓN
    # =====================================================
    print("Seleccionando concepto: DISTRIBUCION")

    combo_concepto = auto.ComboBoxControl(Name="cmbConcepto")
    combo_concepto.Click()

    opcion = auto.ListItemControl(RegexName="DISTRIBUCION")
    opcion.Click()

    # =====================================================
    # 7. 🔢 GENERAR E INGRESAR N° GR
    # =====================================================
    codigo_ngr = generar_codigo_ngr()
    print(f"NGR generado: {codigo_ngr}")

    ngr_input = Registro.EditControl(Name="txtGuiaRemision")
    ngr_input.SendKeys(codigo_ngr)

    ups_boton = Registro.ButtonControl(
        Name="...", foundIndex=5
    )  # es el botom 5, comparten el mismo nombre generico
    # ups_boton.BoundingRectangle
    ups_boton.Click()

    auto.SendKeys("{Enter}")

    # referencia
    referencia_input = Registro.EditControl(Name="txtReferencia")
    referencia_input.SendKeys("B.O.T")

    # hagamos el click derecho a la tabla para que nos salga la opcion de ingresar producto
    auto.Click(810, 410)
    sleep(0.3)
    auto.SendKeys("{CONTROL}{INSERT}")

    sleep(0.5)

    # agregar producto

    Codigo_input = Registro.EditControl(Name="txtCodigo")
    Codigo_input.SendKeys("30588")  # 30588
    auto.SendKeys("{Enter}")

    sleep(0.5)

    Codigo_input = Registro.EditControl(Name="txtLote")
    Codigo_input.SendKeys("2080015")  # 2080015
    auto.SendKeys("{Enter}")

    sleep(0.5)

    Codigo_input = Registro.EditControl(Name="txtCantidad")
    Codigo_input.SendKeys("27")
    auto.SendKeys("{Enter}")

    sleep(0.5)

    agregar_boton = Registro.ButtonControl(
        Name="cmdAceptar"
    )  # es el botom 5, comparten el mismo nombre generico
    # ups_boton.BoundingRectangle
    agregar_boton.Click()

    sleep(0.5)

    # vale apartir de ahora sera el flujo para agregar mas productos a la nota de ingreso dependiendo de la cantidad de productos que haya en la nota de salida realizada pro ksalud, si la nota tiene 25 productos ps 25 productos se agregaran, sera un bucle que terminara cuando ya no haya productos. de alli el siguiente paso es guaradar la nota (darle al botom guardar)

    # este codigo es para agregar un nuevo producto xd. podria ser una funcion tipo agregar producto y llamarla tambien xd. nos ahorrariamos muchas lineas de texto ya que si una nota de salida tiene 300 productos imaginate 3 lineas por 300 son 900, aunque creo que en el bucle eso no importa, corrigeme si es asi
    auto.Click(810, 410)
    sleep(0.3)
    auto.SendKeys("{CONTROL}{INSERT}")

    # agregar producto

    Codigo_input = Registro.EditControl(Name="txtCodigo")
    Codigo_input.SendKeys("30588")  # 30588
    auto.SendKeys("{Enter}")

    sleep(0.5)

    Codigo_input = Registro.EditControl(Name="txtLote")
    Codigo_input.SendKeys("2080015")  # 2080015
    auto.SendKeys("{Enter}")

    sleep(0.5)

    Codigo_input = Registro.EditControl(Name="txtCantidad")
    Codigo_input.SendKeys("52")
    auto.SendKeys("{Enter}")

    sleep(0.5)

    agregar_boton = Registro.ButtonControl(
        Name="cmdAceptar"
    )  # es el botom 5, comparten el mismo nombre generico
    # ups_boton.BoundingRectangle
    agregar_boton.Click()

    sleep(0.5)


if __name__ == "__main__":
    main()
