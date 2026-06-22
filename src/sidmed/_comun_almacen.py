from re import Pattern, compile
from time import sleep

from comtypes import COMError
from retry import retry
from uiautomation import (
    ButtonControl,
    DocumentControl,
    TitleBarControl,
    WindowControl,
)

from src.logger import logger


def guardar() -> None:
    CmdSave: ButtonControl = ButtonControl(Name="CmdSave")
    CmdSave.Click()
    sleep(0.5)


VENTANA_ERROR = WindowControl(Name="Program Error")
BOTON_IGNORAR_ERROR = VENTANA_ERROR.ButtonControl(Name="Ignore")
CORRELATIVO_PATTERN: Pattern = compile(
    r"Se grabó correctamente la Nota de (Ingreso|Salida) N° (\d+)"
)


@retry(tries=3, backoff=2, delay=2, exceptions=(COMError,))
def close_doc_windows() -> None:
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
