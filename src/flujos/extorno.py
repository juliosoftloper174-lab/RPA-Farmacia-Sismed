import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from time import sleep

import uiautomation as auto
from uiautomation import Click, SendKeys, WindowControl

from database.conexion import ejecutar_sp_update_estado
from src.config import SISMED_PASSWORD, SISMED_USERNAME
from src.flujos._login import login
from src.helpers.comun.input import escribir_input
from src.helpers.comun.windows import get_system_info_panel
from src.helpers.pedido.farmacia import seleccionar_farmacia_por_codigo
from src.logger import logger
from src.models.extorno import Extorno
from src.models.Medicamento import Medicamento


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


# =========================================================
# 🔹 SELECCIÓN DE PEDIDO Y ANULACIÓN
# =========================================================


def _leer_texto_celda(celda) -> str:
    try:
        edit = celda.EditControl(Name="Text1")
        if edit.Exists(maxSearchSeconds=0.5):
            return edit.GetValuePattern().Value.strip()
    except Exception:
        pass

    if celda.Name:
        return celda.Name.strip()

    for hijo in celda.GetChildren():
        texto = _leer_texto_celda(hijo)
        if texto:
            return texto
    return ""


def _leer_codigos_grd_deta(ventana_venta: WindowControl) -> set[str]:
    tabla = ventana_venta.TableControl(Name="GrdDeta")
    if not tabla.Exists(maxSearchSeconds=3):
        logger.debug("[EXTORNO] No se encontró GrdDeta aún")
        return set()

    view = tabla.TableControl(Name="View 1")
    if not view.Exists(maxSearchSeconds=3):
        return set()

    codigos = set()
    for fila in view.GetChildren():
        if "Group" in str(fila.ControlType):
            continue

        celdas = fila.GetChildren()
        if len(celdas) < 3:
            continue

        codigo = _leer_texto_celda(celdas[2])
        if codigo and codigo.lower() != "codigo":
            codigos.add(codigo)

    logger.debug(f"[EXTORNO] Códigos leídos en GrdDeta: {codigos}")
    return codigos


def _seleccionar_pedido_correcto(
    ventana_venta: WindowControl, medicamentos: list[Medicamento]
) -> None:
    codigos_esperados = {m.codigo.strip() for m in medicamentos}
    logger.debug(f"[EXTORNO] Códigos esperados: {codigos_esperados}")

    tabla = ventana_venta.TableControl(Name="GrdSel")
    if not tabla.Exists(maxSearchSeconds=5):
        raise RuntimeError("No se encontró la tabla 'GrdSel'")

    view = tabla.TableControl(Name="View 1")
    if not view.Exists(maxSearchSeconds=5):
        raise RuntimeError("No se encontró 'View 1' dentro de 'GrdSel'")

    filas = [h for h in view.GetChildren() if "Group" not in str(h.ControlType)]
    logger.info(f"[EXTORNO] Filas en GrdSel: {len(filas)}")

    if not filas:
        raise RuntimeError("No se encontraron filas en GrdSel")

    codigos_anteriores: set[str] = set()

    for idx, fila in enumerate(filas, start=1):
        logger.debug(f"[EXTORNO] Revisando fila {idx}")

        # Seleccionar fila: primero InvokePattern, luego click en celda de cliente
        seleccionado = False
        try:
            patron_invoke = fila.GetInvokePattern()
            if patron_invoke:
                patron_invoke.Invoke()
                logger.debug(f"[EXTORNO] Fila {idx} activada vía InvokePattern")
                seleccionado = True
        except Exception as e:
            logger.debug(f"[EXTORNO] InvokePattern no disponible: {e}")

        if not seleccionado:
            celdas_fila = fila.GetChildren()
            # Intentar click en celda de cliente (índice 4 según headers: T/D, Numero, Fecha, DNI, Cliente...)
            if len(celdas_fila) > 4:
                celdas_fila[4].Click()
                logger.debug(f"[EXTORNO] Fila {idx} click en celda Cliente")
            elif celdas_fila:
                celdas_fila[0].Click()
                logger.debug(f"[EXTORNO] Fila {idx} click en primera celda")
            else:
                fila.Click()
                logger.debug(f"[EXTORNO] Fila {idx} click en fila")

        sleep(2.5)

        codigos_encontrados = _leer_codigos_grd_deta(ventana_venta)

        # Si GrdDeta no cambió, puede estar mostrando datos de la fila anterior.
        reintentos = 0
        while codigos_encontrados == codigos_anteriores and codigos_encontrados and reintentos < 2:
            logger.debug("[EXTORNO] GrdDeta parece no haber cambiado, reintentando...")
            sleep(2)
            codigos_encontrados = _leer_codigos_grd_deta(ventana_venta)
            reintentos += 1

        codigos_anteriores = codigos_encontrados

        if codigos_esperados == codigos_encontrados:
            logger.info(f"[EXTORNO] Pedido correcto encontrado en fila {idx}")
            return

        logger.debug(
            f"[EXTORNO] Fila {idx} no coincide. Esperado: {codigos_esperados}, Encontrado: {codigos_encontrados}"
        )

    raise RuntimeError("No se encontró pedido con los medicamentos esperados")


def _completar_anulacion() -> None:
    logger.debug("[EXTORNO] Completando anulación")

    ventana_venta = WindowControl(Name="Seleccionar Venta")
    if ventana_venta.Exists(maxSearchSeconds=3):
        _click_button_flexible(ventana_venta, "Seleccionar", max_wait=3)
        logger.debug("[EXTORNO] Click en Seleccionar")

        for _ in range(10):
            if not ventana_venta.Exists(maxSearchSeconds=0.5):
                break
            sleep(0.5)
    else:
        raise RuntimeError("No se encontró 'Seleccionar Venta' para seleccionar pedido")

    registro = WindowControl(Name="Registro de Consumo")
    if not registro.Exists(maxSearchSeconds=5):
        raise RuntimeError("No se reencontró 'Registro de Consumo'")

    btn_del = registro.ButtonControl(Name="CmdDel")
    if not btn_del.Exists(maxSearchSeconds=3):
        raise RuntimeError("No se encontró el botón 'CmdDel'")
    btn_del.Click()
    logger.debug("[EXTORNO] Click en CmdDel")
    sleep(1.5)

    ventana_anular = WindowControl(Name="Anular")
    if not ventana_anular.Exists(maxSearchSeconds=5):
        raise RuntimeError("No apareció la ventana 'Anular'")

    btn_anular = ventana_anular.ButtonControl(Name="Anular")
    if not btn_anular.Exists(maxSearchSeconds=3):
        raise RuntimeError("No se encontró el botón 'Anular' en ventana Anular")
    btn_anular.Click()
    logger.debug("[EXTORNO] Click en Anular")
    sleep(1.5)

    dialogo_aviso = WindowControl(Name="Aviso")
    if not dialogo_aviso.Exists(maxSearchSeconds=5):
        raise RuntimeError("No apareció el diálogo 'Aviso'")

    btn_si = dialogo_aviso.ButtonControl(Name="Sí")
    if not btn_si.Exists(maxSearchSeconds=3):
        raise RuntimeError("No se encontró el botón 'Sí' en diálogo Aviso")
    btn_si.Click()
    logger.debug("[EXTORNO] Click en Sí")

    for _ in range(10):
        if not dialogo_aviso.Exists(maxSearchSeconds=0.5):
            break
        sleep(0.5)

    logger.success("[EXTORNO] Anulación completada")


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

    sleep(1)
    _seleccionar_pedido_correcto(ventana_venta, extorno.medicamentos)
    _completar_anulacion()


def procesar_extorno(extorno: Extorno) -> dict:
    login(SISMED_USERNAME, SISMED_PASSWORD)
    navegar_a_extorno(extorno.farmacia)
    buscar_venta_extorno(extorno)

    if extorno.update_key:
        logger.debug("[EXTORNO] Actualizando estado BD (00)...")
        ejecutar_sp_update_estado(extorno.update_key, "00")

    return {"estado": "OK", "correlativo": None}


def procesar_extornos(extornos: tuple[Extorno, ...]) -> dict:
    total = len(extornos)
    logger.info(f"[EXTORNO] Iniciando procesamiento de {total} extorno(s)")

    login(SISMED_USERNAME, SISMED_PASSWORD)
    ok_count = 0
    error_count = 0

    for idx, extorno in enumerate(extornos, start=1):
        try:
            logger.info(f"[EXTORNO] {idx}/{total}")
            navegar_a_extorno(extorno.farmacia)
            buscar_venta_extorno(extorno)

            if extorno.update_key:
                logger.debug(f"[EXTORNO] {idx}/{total} Actualizando estado BD (00)...")
                ejecutar_sp_update_estado(extorno.update_key, "00")

            logger.success(f"[EXTORNO] {idx}/{total} OK")
            ok_count += 1

        except Exception as e:
            logger.error(f"[EXTORNO] {idx}/{total} error: {e}")
            error_count += 1

    return {"total": total, "ok": ok_count, "error": error_count}


if __name__ == "__main__":
    extorno = Extorno(
        farmacia="06732F02",
        cliente_dni="002964401",
        fecha="20/07/2026",
        tipo_documento="CE",
        medicamentos=[
            Medicamento(codigo="19499", cantidad=8),
        ],
    )
    procesar_extorno(extorno)
