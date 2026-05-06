from time import sleep

from uiautomation import ButtonControl, TextControl, WindowControl


from src.sidmed.ingreso import seleccionar_combo_por_texto

ALMACEN_WINDOW: WindowControl = WindowControl(
    searchDepth=1, Name="ALMACEN - MINSA SISMED"
)
BOTON_CLOOSE_ALMACEN = ALMACEN_WINDOW.ButtonControl(Name="Cerrar")
AVISO_DIALOG: WindowControl = ALMACEN_WINDOW.WindowControl(searchDepth=1, Name="Aviso")
CORRELATIVO_SAVED_TEXT: TextControl = AVISO_DIALOG.TextControl(
    NameRegex=r"Se grabó correctamente la Nota de (Ingreso|Salida) N° \d+"
)
BOTON_ACEPTAR_AVISO: ButtonControl = AVISO_DIALOG.ButtonControl(Name="Aceptar")

MINSA_DIALOG: WindowControl = ALMACEN_WINDOW.WindowControl(
    searchDepth=1, Name="MINSA SISMED"
)
ERROR_TEXT: TextControl = MINSA_DIALOG.TextControl(searchDepth=1, foundIndex=1)

# DOCUMENT_CONTROL: DocumentControlTypeId
REPORT_DESIGNER_WINDOW = WindowControl(
    Name="Report Designer - rptalmregisting.frx - Page 1"
)
BOTON_CLOOSE_REPORT_DESIGNER = REPORT_DESIGNER_WINDOW.ButtonControl(Name="Cerrar")

ALMACENPRINCIPAL_WINDOW = WindowControl(Name="ALMACEN - MINSA SISMED")
BOTON_CLOOSE_ALMACEN_PRINCIPAL = ALMACENPRINCIPAL_WINDOW.ButtonControl(Name="Cerrar")

VENTANA_ERROR = WindowControl(Name="Program Error")
BOTON_IGNORAR_ERROR = VENTANA_ERROR.ButtonControl(Name="Ignore")


def test_children(monkeypatch):
    # Se cierra el aviso
    if AVISO_DIALOG.Exists(3):
        print("Cerrando ventana aviso...")
        AVISO_DIALOG.SetFocus()
        sleep(0.3)
        BOTON_ACEPTAR_AVISO.Click()
        sleep(4)

        # CERRAR VENTANA DE ERROR

    if VENTANA_ERROR.Exists(3):
        print("Cerrando ventana de error...")
        VENTANA_ERROR.SetFocus()
        sleep(0.3)
        BOTON_IGNORAR_ERROR.Click()
        sleep(4)

    if REPORT_DESIGNER_WINDOW.Exists(3):
        print("Cerrando Report Designer...")
        REPORT_DESIGNER_WINDOW.SetFocus()
        sleep(0.3)
        BOTON_CLOOSE_REPORT_DESIGNER.Click()
        sleep(4)

    # CERRAR VENTANA DE ALMACEN

    if ALMACEN_WINDOW.Exists(3):
        print("Cerrando ventana de Almacén...")
        ALMACEN_WINDOW.SetFocus()
        sleep(0.3)
        BOTON_CLOOSE_ALMACEN.Click()
        sleep(1)

    # AHORA DEBEMMOS CERRAR LA VENTANA PRINCIPAL

    if ALMACENPRINCIPAL_WINDOW.Exists(3):
        print("Cerrando ventana principal de Almacén...")
        ALMACENPRINCIPAL_WINDOW.SetFocus()
        sleep(0.3)
        BOTON_CLOOSE_ALMACEN_PRINCIPAL.Click()
        sleep(1)
