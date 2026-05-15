from uiautomation import WindowControl
import logging

logger = logging.getLogger(__name__)


def verificar_aviso_sismed(timeout: float = 1):
    """not uset, may be deletable"""

    aviso = WindowControl(Name="Aviso")

    if aviso.Exists(timeout):

        mensaje = aviso.TextControl(searchDepth=1).Name.strip()

        boton = aviso.ButtonControl(Name="Aceptar")

        if boton.Exists(1):
            boton.Click()

        logger.error(f"SISMED: {mensaje}")

        raise RuntimeError(f"SISMED: {mensaje}")


def click_boton(control, nombre_error: str, timeout: float = 2):

    if not control.Exists(timeout):
        raise RuntimeError(f"UI: No se encontró botón/control: {nombre_error}")

    try:
        control.Click()

    except Exception as e:
        raise RuntimeError(f"UI: Error haciendo click en '{nombre_error}' -> {str(e)}")


def escribir_input(control, texto, nombre_error: str, timeout: float = 2):

    if not control.Exists(timeout):
        raise RuntimeError(f"UI: No se encontró input/control: {nombre_error}")

    try:
        control.SendKeys(str(texto))

    except Exception as e:
        raise RuntimeError(f"UI: Error escribiendo en '{nombre_error}' -> {str(e)}")


def obtener_texto(control, nombre_error: str, timeout: float = 2) -> str:

    if not control.Exists(timeout):
        raise RuntimeError(f"UI: No se encontró texto/control: {nombre_error}")

    texto = control.Name.strip()

    if not texto:
        raise RuntimeError(f"UI: El texto de '{nombre_error}' está vacío")

    return texto


from time import sleep


def cerrar_ventana_segura(ventana, boton, nombre: str, reintentos: int = 3) -> None:

    if not ventana.Exists(1):
        return None

    for intento in range(reintentos):

        try:

            logger.info(f"Cerrando ventana: {nombre} " f"(intento {intento + 1})")

            # ventana.SetFocus()

            sleep(1)

            boton.Click()

            sleep(2)

            # 🔥 Si ya no existe salimos
            if not ventana.Exists(1):
                return None

            pass

        except Exception as e:

            logger.warning(f"Error cerrando {nombre}: {e}")

        sleep(1)

    logger.warning(f"No se pudo confirmar cierre de: {nombre}")
    return None
