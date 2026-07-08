from time import sleep
from src.logger import logger
import uiautomation as auto
from uiautomation import TableControl

from src.helpers.comun.input import escribir_input
from src.helpers.comun.ventana import esperar_ventana
from src.models.Medicamento import Medicamento


def agregar_producto(medicamento: Medicamento) -> None:

    # 🔹 Nueva fila
    auto.SendKeys("{CONTROL}{INSERT}")
    sleep(0.3)

    # 🔹 Abrir ventana
    auto.SendKeys("{Enter}")

    ventana = esperar_ventana("Seleccionar medicamento")

    # 🔹 Ordenar por código
    try:
        header_codigo = ventana.HeaderControl(Name="Código")
        if header_codigo.Exists(3):
            header_codigo.Click()
        else:
            raise Exception("Header no encontrado")
    except Exception as e:
        logger.info("Fallback click código:", e)
        auto.Click(360, 140)
        sleep(0.3)

    # 🔹 Buscar medicamento por código
    txt_busca = ventana.EditControl(Name="TxtBusca")
    escribir_input(txt_busca, medicamento.codigo)

    sleep(0.5)
    txt_busca.SendKeys("{Enter}")
    sleep(1)  # 🔥 importante: esperar que cargue la grilla

    # 🔹 Click en botón "Seleccionar"
    try:
        btn_seleccionar = ventana.ButtonControl(Name="Seleccionar")
        if btn_seleccionar.Exists(3):
            btn_seleccionar.Click()
        else:
            raise Exception("Botón no encontrado")
    except Exception as e:
        logger.info("Fallback botón seleccionar:", e)
        auto.Click(687, 638)  # fallback real que detectaste

    # 🔹 Ingresar cantidad
    sleep(0.5)
    auto.SendKeys(str(medicamento.cantidad))

    sleep(0.3)

    # 🔹 Confirmar línea
    auto.SendKeys("{CONTROL}{INSERT}")
    auto.SendKeys("{CONTROL}{DELETE}")


def agregar_productos(medicamentos: tuple[Medicamento, ...]):
    for m in medicamentos:
        agregar_producto(m)
