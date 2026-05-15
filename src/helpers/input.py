from time import sleep

from uiautomation import Control
from _ctypes import COMError
from retry import retry


# @retry(tries=3, backoff=2, delay=2, exceptions=(COMError,))
def escribir_input(control: Control, texto: str) -> None:

    if not control.Exists():
        raise Exception("Input no encontrado")

    control.SetFocus()
    sleep(0.2)
    control.SendKeys(texto)
    return None
