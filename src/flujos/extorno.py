import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from time import sleep

import uiautomation as auto
from uiautomation import Click, SendKeys, WindowControl

from src.config import SISMED_PASSWORD, SISMED_USERNAME
from src.flujos._login import login
from src.helpers.comun.input import escribir_input
from src.helpers.comun.windows import get_system_info_panel
from src.helpers.pedido.farmacia import seleccionar_farmacia_por_codigo
from src.logger import logger
from src.models.extorno import Extorno


def navegar_a_extorno(farmacia_codigo: str) -> None:
    logger.debug(f"[EXTORNO] Navegando a farmacia={farmacia_codigo}")

    Click(355, 115)

    pane = get_system_info_panel()

    pane.SendKeys("{RIGHT}")

    ventana: WindowControl = WindowControl(Name="Selección de Farmacias")
    for attempt in range(3):
        pane.SendKeys("{Enter}")
        if ventana.Exists():
            break

    if not ventana.Exists():
        raise RuntimeError(
            "No se encontró la ventana de selección de farmacias después de 3 intentos"
        )

    seleccionar_farmacia_por_codigo(farmacia_codigo)

    sleep(0.5)

    for _ in range(2):
        SendKeys("{DOWN}")

    SendKeys("{TAB}")
    SendKeys("{RIGHT}")
    SendKeys("{Enter}")

    sleep(0.5)

    logger.debug("[EXTORNO] Navegación completada")


def buscar_venta_extorno(extorno: Extorno) -> None:
    logger.debug("[EXTORNO] Abriendo búsqueda de venta (CmdSeek)")

    ventana = WindowControl(Name="Registro de Consumo")
    if not ventana.Exists(maxSearchSeconds=5):
        raise RuntimeError("No se encontró la ventana 'Registro de Consumo'")

    btn_seek = ventana.ButtonControl(Name="CmdSeek")
    if not btn_seek.Exists(maxSearchSeconds=3):
        raise RuntimeError("No se encontró el botón 'CmdSeek'")
    btn_seek.Click()

    ventana_venta = WindowControl(Name="Seleccionar Venta")
    if not ventana_venta.Exists(maxSearchSeconds=5):
        raise RuntimeError("No apareció la ventana 'Seleccionar Venta'")

    fecha_limpia = extorno.fecha.replace("/", "")
    logger.debug(f"[EXTORNO] Buscando venta desde {fecha_limpia} hasta {fecha_limpia}")

    txt_desde = ventana_venta.EditControl(Name="TxtDesde")
    escribir_input(txt_desde, fecha_limpia)

    txt_hasta = ventana_venta.EditControl(Name="TxtHasta")
    escribir_input(txt_hasta, fecha_limpia)

    logger.debug("[EXTORNO] Marcando checkbox 'Por Cliente DNI'")
    chk_dni = ventana_venta.CheckBoxControl(Name="Por Cliente DNI")
    if not chk_dni.Exists(maxSearchSeconds=3):
        raise RuntimeError("No se encontró el checkbox 'Por Cliente DNI'")
    chk_dni.Click()

    logger.success("[EXTORNO] Checkpoint alcanzado: checkbox marcado")


def procesar_extorno(extorno: Extorno) -> None:
    login(SISMED_USERNAME, SISMED_PASSWORD)
    navegar_a_extorno(extorno.farmacia)
    buscar_venta_extorno(extorno)


def procesar_extornos(extornos: tuple[Extorno, ...]) -> dict:
    total = len(extornos)
    logger.info(f"[EXTORNO] Iniciando procesamiento de {total} extorno(s)")

    login(SISMED_USERNAME, SISMED_PASSWORD)

    for idx, extorno in enumerate(extornos, start=1):
        try:
            logger.info(f"[EXTORNO] {idx}/{total}")
            navegar_a_extorno(extorno.farmacia)
            buscar_venta_extorno(extorno)
        except Exception as e:
            logger.error(f"[EXTORNO] {idx}/{total} error: {e}")

    return {"total": total, "ok": 0, "error": 0}


if __name__ == "__main__":
    extorno = Extorno(
        farmacia="06732F02",
        cliente_dni="002964401",
        fecha="20/07/2026",
        medicamentos=[],
    )
    procesar_extorno(extorno)
