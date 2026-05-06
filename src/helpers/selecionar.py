from asyncio import sleep
import uiautomation as auto

from uiautomation import ListItemControl


def seleccionar_combo_por_texto(nombre_combo: str, texto_objetivo: str):
    combo = auto.ComboBoxControl(Name=nombre_combo)

    if not combo.Exists():
        raise Exception(f"No se encontró combo: {nombre_combo}")

    combo.Click()
    for i in range(10):  # NOTE: Generic way to go up, not necesarily eficient.
        auto.SendKeys("{UP}")
    children = combo.GetChildren()
    elementos = [child.Name.strip() for child in children]

    for child in children:
        if child.Name.strip() == texto_objetivo:
            child.Click()
            return

    raise Exception(f"No se encontró el texto: {texto_objetivo}")


def seleccionar_combo_por_texto_con_autoenter(nombre_combo: str, texto_objetivo: str):
    """
    Aqui, si pones Up, LEFT, RIGHT DOWN u otra tecla validad, se autopresiona ENTER,, tener cuidado.

    NOTE: Cannot click by list index (value of the combo box), combo box indexes and list indexes does not match.
    NOTE: You can natively select by label, but not necesarily sets the wanted option.
    NOTE: MAy be safer but not change resilent to search by a fixed amount of indexed, hardcoded.
    NOTE: This funtion may need optimization.
    """
    combo = auto.ComboBoxControl(Name=nombre_combo)

    if not combo.Exists():
        raise Exception(f"No se encontró combo: {nombre_combo}")

    # NOTE: Genereic way to set the visible options to start with the first letter of the target, not necesarily efficient.
    combo.Click()
    combo.SendKeys(texto_objetivo.strip()[0])

    combo.Click()
    children = combo.GetChildren()
    elementos: list[ListItemControl] = [child.Name.strip() for child in children]
    # TODO: List all options, because some mey be unavailable, this can be done by going up an down for a while.
    index = elementos.index(texto_objetivo)
    print(f"Elementos encontrados en combo {nombre_combo}: {elementos}")
    for child in children:
        if child.Name.strip() == texto_objetivo:
            child.Click()
            sleep(0.3)
            # TODO: Find a way to check the correct test is selected, because now, the value is index, no name.
            value = combo.GetValuePattern().Value
            # TODO: Check with OCR
            combo.CaptureToImage(f"./temp/screenshot_{nombre_combo}.png")
            print(f"Valor seleccionado: {value}")
            return

    raise Exception(f"No se encontró el texto: {texto_objetivo}")
