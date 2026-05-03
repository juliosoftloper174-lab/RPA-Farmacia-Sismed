from time import sleep

import uiautomation as auto
from uiautomation import Click, SendKeys
from ..helpers.ui_helper import normalizar, obtener_texto_edit
from uiautomation import WindowControl


def seleccionar_farmacia_por_codigo(codigo_objetivo: str):

    codigo_objetivo = normalizar(codigo_objetivo)

    ventana: WindowControl = WindowControl(Name="Selección de Farmacias")

    if not ventana.Exists(3):
        raise Exception("No se encontró la ventana")

    ventana.SetActive()
    sleep(0.5)

    filas = []

    for control, _ in auto.WalkControl(ventana):
        if control.ControlTypeName == "CustomControl" and control.Name.isdigit():
            filas.append(control)

    filas.sort(key=lambda x: int(x.Name))

    for fila in filas:
        try:
            celdas = fila.GetChildren()

            if len(celdas) >= 2:
                texto = obtener_texto_edit(celdas[1])
                texto = normalizar(texto)

                if codigo_objetivo == texto:
                    fila.Click()
                    sleep(0.2)
                    auto.SendKeys("{Enter}")
                    return

        except Exception as e:
            print(f"Error occurred while processing fila: {e}")
            continue

    raise Exception(f"No se encontró farmacia con código: {codigo_objetivo}")
