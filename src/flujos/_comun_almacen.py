from re import Pattern, compile
from time import sleep, time

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


@retry(tries=3, backoff=2, delay=1, exceptions=(COMError,))
def extraer_correlativo_almacen(timeout: float = 90.0) -> str:
    ALMACEN_WINDOW: WindowControl = WindowControl(
        searchDepth=1, Name="ALMACEN - MINSA SISMED"
    )

    inicio = time()
    while (time() - inicio) < timeout:
        try:
            aviso = ALMACEN_WINDOW.WindowControl(searchDepth=1, Name="Aviso")

            if aviso.Exists(0):
                mensaje: str = aviso.TextControl(searchDepth=1).Name.strip()
                logger.debug(f"{mensaje = }.")

                accept_button: ButtonControl = aviso.ButtonControl(Name="Aceptar")
                accept_button.GetInvokePattern().Invoke()

                close_doc_windows()

                if correlative_match := CORRELATIVO_PATTERN.search(mensaje):
                    return correlative_match.group(2)

                raise ValueError(f"SISMED: {mensaje}")

            minsa = ALMACEN_WINDOW.WindowControl(searchDepth=1, Name="MINSA SISMED")

            if minsa.Exists(0):
                mensaje_error: str = minsa.TextControl(
                    searchDepth=1, foundIndex=1
                ).Name.strip()
                raise ValueError(f"MINSA: {mensaje_error}")

        except COMError as e:
            logger.warning(f"[CORRELATIVO] Error COM al buscar aviso: {e}")

        sleep(1)

    raise RuntimeError(
        f"No se encontró ni correlativo ni mensaje de error después de {timeout}s."
    )


def cerrar_ventana_registro(nombre_ventana: str = "Registro de Ingresos .") -> None:
    registro = WindowControl(Name=nombre_ventana)
    if registro.Exists(2):
        title_bar = registro.TitleBarControl(searchDepth=1)
        close_button = title_bar.ButtonControl(searchDepth=1, Name="Cerrar")
        if close_button.Exists():
            close_button.GetInvokePattern().Invoke()


def cerrar_ventana_salida_guardada() -> None:
    """Cierra la ventana de registro de salidas tras guardar.

    En versiones anteriores de SISMED la ventana cambiaba de nombre a E-XXXXX.
    En la versión actual de producción conserva el nombre 'Registro de Salidas '.
    """
    for intento in range(5):
        try:
            ventana = WindowControl(Name="Registro de Salidas ")
            if ventana.Exists(1):
                title_bar = ventana.TitleBarControl(searchDepth=1)
                close_button = title_bar.ButtonControl(searchDepth=1, Name="Cerrar")
                if close_button.Exists():
                    close_button.GetInvokePattern().Invoke()
                    sleep(0.5)
                    confirmacion = WindowControl(Name="Aviso")
                    if confirmacion.Exists(2):
                        si = confirmacion.ButtonControl(Name="Sí")
                        if si.Exists():
                            si.Click()
                return
        except COMError as e:
            logger.warning(
                f"[CERRAR SALIDA] Error COM en intento {intento + 1}: {e}"
            )
        sleep(1)
    logger.warning("No se encontró ventana 'Registro de Salidas ' para cerrar")


def cerrar_sismed() -> None:
    almacen_window: WindowControl = WindowControl(
        searchDepth=1, Name="ALMACEN - MINSA SISMED"
    )
    try:
        almacen_window.GetWindowPattern().Close()
    except Exception:
        logger.debug("Ventana 'ALMACEN - MINSA SISMED' no presente, omitiendo.")

    minsa_sismed_window: WindowControl = WindowControl(
        searchDepth=1, Name="MINSA SISMED"
    )
    if not (windows_pattern := minsa_sismed_window.GetWindowPattern()):
        raise RuntimeError("No se encontró la ventana principal de Sismed.")
    windows_pattern.Close()
