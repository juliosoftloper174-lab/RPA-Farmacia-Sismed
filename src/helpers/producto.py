from time import sleep

import uiautomation as auto
from uiautomation import TableControl

from src.helpers.input import escribir_input
from src.helpers.ventana import esperar_ventana
from src.models.producto import Producto


def obtener_nombre_base(nombre_completo: str) -> str:
    return nombre_completo.split("-")[0].strip()


def agregar_producto(producto: Producto) -> None:

    auto.SendKeys("{CONTROL}{INSERT}")
    auto.SendKeys("{Enter}")

    ventana = esperar_ventana("Seleccionar medicamento")
    txt_busca = ventana.EditControl(Name="TxtBusca")

    nombre_base = obtener_nombre_base(producto.nombre)
    escribir_input(txt_busca, nombre_base)

    sleep(1)
    txt_busca.SendKeys("{Enter}")
    sleep(1)

    table_med = TableControl(Name="GrdMed")
    view_1 = table_med.TableControl(searchDepth=1, Name="View 1")

    for i in range(1, 18):
        row = view_1.CustomControl(searchDepth=1, Name=str(i))

        try:
            description_cell = row.DataItemControl(searchDepth=1, foundIndex=1)
            description_edit = description_cell.EditControl(searchDepth=1, Name="Text1")
            value = description_edit.GetValuePattern().Value

            if not value:
                continue

            if value.strip().lower() == producto.nombre.strip().lower():
                row.Click()
                row.SendKeys("{Enter}")
                break

        except:
            continue

    auto.SendKeys(str(producto.cantidad))
    auto.SendKeys("{CONTROL}{INSERT}")
    auto.SendKeys("{CONTROL}{DELETE}")


def agregar_productos(productos: tuple[Producto, ...]):
    for p in productos:
        agregar_producto(p)
