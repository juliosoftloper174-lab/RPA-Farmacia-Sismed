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


def _debug_children(control, label: str = "") -> None:
    try:
        children = control.GetChildren()
        names = [f"{c.ControlType.__name__} Name='{c.Name}'" for c in children]
        logger.debug(f"[EXTORNO DEBUG] {label}: {names}")
    except Exception as e:
        logger.debug(f"[EXTORNO DEBUG] {label}: error listando hijos: {e}")


def _click_button_flexible(
    parent,
    name: str,
    alternatives: list[str] | None = None,
    max_wait: float = 3,
) -> None:
    alternatives = alternatives or []
    candidates = [name] + alternatives
    for candidate in candidates:
        btn = parent.ButtonControl(Name=candidate)
        if btn.Exists(maxSearchSeconds=max_wait):
            btn.Click()
            logger.debug(f"[EXTORNO] Click en botón Name='{candidate}'")
            return
    _debug_children(parent, f"botones disponibles buscando '{name}'")
    raise RuntimeError(f"No se encontró botón '{name}' (alternativas: {alternatives})")


def _click_buscar(parent) -> None:
    _click_button_flexible(parent, "Buscar", ["CmdBuscar", "Buscar"], max_wait=2)


def _buscar_por_dni(ventana_venta, documento: str) -> None:
    logger.debug("[EXTORNO] Flujo DNI: escribiendo TxtDNICli")
    txt_dni = ventana_venta.EditControl(Name="TxtDNICli")
    if not txt_dni.Exists(maxSearchSeconds=3):
        _debug_children(ventana_venta, "controles tras marcar DNI")
        raise RuntimeError("No apareció el input 'TxtDNICli' tras marcar checkbox")
    escribir_input(txt_dni, documento)
    sleep(0.5)
    _click_buscar(ventana_venta)


def _buscar_por_otro_documento(ventana_venta, documento: str) -> None:
    logger.debug("[EXTORNO] Flujo no-DNI: abriendo selector de clientes")

    sleep(0.3)
    SendKeys("{TAB}")
    sleep(0.2)
    SendKeys("{Enter}")
    logger.debug("[EXTORNO] Tab+Enter enviado para abrir 'Seleccionar Clientes'")
    sleep(2)

    ventana_clientes = WindowControl(Name="Seleccionar Clientes")
    if not ventana_clientes.Exists(maxSearchSeconds=5):
        _debug_children(auto.GetRootControl(), "ventanas abiertas tras Tab+Enter")
        raise RuntimeError("No apareció la ventana 'Seleccionar Clientes'")

    logger.debug("[EXTORNO] Ventana 'Seleccionar Clientes' detectada")
    _debug_children(ventana_clientes, "controles iniciales Seleccionar Clientes")

    header_numero = ventana_clientes.HeaderControl(Name="Numero")
    if not header_numero.Exists(maxSearchSeconds=2):
        _debug_children(ventana_clientes, "headers disponibles")
        raise RuntimeError("No se encontró el header 'Numero'")
    header_numero.Click()
    logger.debug("[EXTORNO] Click en header 'Numero'")
    sleep(0.5)

    txt_busca = ventana_clientes.EditControl(Name="TxtBusca")
    if not txt_busca.Exists(maxSearchSeconds=2):
        _debug_children(ventana_clientes, "inputs disponibles")
        raise RuntimeError("No se encontró el input 'TxtBusca'")
    escribir_input(txt_busca, documento)
    logger.debug(f"[EXTORNO] Documento '{documento}' escrito en TxtBusca")
    sleep(0.3)

    _click_buscar(ventana_clientes)
    sleep(1.5)

    # Seleccionar primera fila por seguridad si hay resultados
    try:
        fila = ventana_clientes.DataItemControl()
        if fila.Exists(maxSearchSeconds=2):
            fila.Click()
            logger.debug("[EXTORNO] Primera fila seleccionada")
            sleep(0.3)
    except Exception as e:
        logger.debug(f"[EXTORNO] No se pudo seleccionar fila: {e}")

    _click_button_flexible(
        ventana_clientes,
        "Seleccionar",
        ["Seleccionar", "CmdSeleccionar", "Aceptar"],
        max_wait=3,
    )

    for _ in range(10):
        if not ventana_clientes.Exists(maxSearchSeconds=0.5):
            break
        sleep(0.5)

    logger.success("[EXTORNO] Cliente seleccionado, volviendo a 'Seleccionar Venta'")

    ventana_venta = WindowControl(Name="Seleccionar Venta")
    if not ventana_venta.Exists(maxSearchSeconds=5):
        raise RuntimeError("No se reencontró la ventana 'Seleccionar Venta'")
    _click_buscar(ventana_venta)


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
    sleep(0.5)

    tipo = extorno.tipo_documento.strip().upper()
    if tipo in ("DNI", "D.N.I", "D.N.I.", "LIBRETA ELECTORAL O  DNI"):
        _buscar_por_dni(ventana_venta, extorno.cliente_dni)
    else:
        _buscar_por_otro_documento(ventana_venta, extorno.cliente_dni)

    logger.success("[EXTORNO] Búsqueda de venta iniciada")


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
        tipo_documento="CE",
        medicamentos=[],
    )
    procesar_extorno(extorno)
