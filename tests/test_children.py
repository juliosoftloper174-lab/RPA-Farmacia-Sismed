from enum import auto
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


MAIN_MENU_WINDOW: WindowControl = WindowControl(searchDepth=1, Name="Menu Principal")
BOTON_CLOOSE_MAIN_WINDOW = MAIN_MENU_WINDOW.ButtonControl(Name="Cerrar")
