from time import sleep

from uiautomation import ComboBoxControl, SendKeys


def seleccionar_combo_click_ciego(combo: ComboBoxControl, posicion: int) -> None:
    if not combo.Exists():
        raise Exception("ComboBox no encontrado")

    combo.SetFocus()
    sleep(0.3)

    for _ in range(posicion):
        combo.Click()
        sleep(0.3)

        SendKeys("{Down}")
        sleep(0.2)

    SendKeys("{Enter}")
    return None
