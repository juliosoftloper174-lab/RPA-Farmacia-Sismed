from time import sleep

from uiautomation import SendKeys, WindowControl

from src.helpers.input import escribir_input


def rellenar_diagnosticos(
    registro_window: WindowControl, lista_diagnosticos: list[str]
) -> None:

    if not lista_diagnosticos:
        raise Exception("Debe haber al menos 1 diagnóstico")

    inputs = [
        registro_window.EditControl(Name="TxtCodCIE"),
        registro_window.EditControl(Name="TxtCodCIE1"),
        registro_window.EditControl(Name="TxtCodCIE2"),
    ]

    for i, diag in enumerate(lista_diagnosticos):
        if i >= len(inputs):
            break

        print(f"Escribiendo diagnóstico {i+1}: {diag}")

        escribir_input(inputs[i], diag)
        sleep(0.3)

        # 🔥 SIEMPRE Enter (incluido el último)
        SendKeys("{Enter}")
        sleep(0.4)

    # =====================================================
    # 🔥 LIMPIAR FILAS VACÍAS (justo después del último Enter)
    # =====================================================

    print("[BOT] Limpiando filas vacías...")

    SendKeys("{CONTROL}{DEL}")
    sleep(0.6)

    SendKeys("{CONTROL}{DEL}")
    sleep(0.6)
    return None
