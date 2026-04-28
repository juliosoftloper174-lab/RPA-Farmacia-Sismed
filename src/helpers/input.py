from time import sleep

from uiautomation import Control


def escribir_input(control: Control, texto: str) -> None:
    if not control.Exists():
        raise Exception("Input no encontrado")

    control.SetFocus()
    sleep(0.2)
    control.SendKeys(texto)
    return None
