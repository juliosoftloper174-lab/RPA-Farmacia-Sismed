from time import sleep


from src.sidmed.ingreso import seleccionar_combo_por_texto


def test_children() -> None:
    sleep(3)
    seleccionar_combo_por_texto("cbotipsum", "SISMED-CENTRALIZADO (SC)")
    return None
