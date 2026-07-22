import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from time import sleep

import uiautomation as auto
from uiautomation import (
    ButtonControl,
    Click,
    ComboBoxControl,
    CustomControl,
    DataItemControl,
    EditControl,
    ListItemControl,
    SendKeys,
    TableControl,
    WindowControl,
)

from database.conexion import ejecutar_sp_update_estado
from src.config import SISMED_PASSWORD, SISMED_USERNAME
from src.flujos._comun_almacen import (
    cerrar_sismed,
    cerrar_ventana_salida_guardada,
    close_doc_windows,
    extraer_correlativo_almacen,
    guardar,
)
from src.flujos._login import (
    esperar_hora_backup_si_aplica,
    login,
    verificar_backup_si_aplica,
)
from src.helpers.comun.input import escribir_input
from src.logger import logger
from src.models.Medicamento import Medicamento
from src.models.Salidas import Salidas
from src.reportes.excel_schema import crear_row_salida
from src.reportes.excel_writer import (
    guardar_movimientos,
    obtener_siguiente_numero_procesado,
)

# =========================================================
# 🔹 HELPERS
# =========================================================


def seleccionar_combo_sismed(nombre_combo: str, texto_objetivo: str, max_intentos=20):
    combo: ComboBoxControl = ComboBoxControl(Name=nombre_combo)

    if not combo.Exists():
        raise Exception(f"No se encontró combo: {nombre_combo}")

    combo.Click()
    sleep(0.5)

    # Baja hasta encontrar el texto
    for i in range(max_intentos):
        # intenta seleccionar visible
        item: ListItemControl = ListItemControl(RegexName=texto_objetivo)

        if item.Exists(1):
            item.Click()
            logger.info(f"✅ Encontrado: {texto_objetivo}")
            return

        SendKeys("{DOWN}")
        sleep(0.2)

    raise Exception(f"❌ No se encontró el concepto: {texto_objetivo}")


# =========================================================
# 🔹 FLUJO BASE
# =========================================================


def navegar_a_salidas() -> WindowControl:
    Click(355, 115)
    sleep(0.3)
    SendKeys("{Enter}")

    sleep(0.3)
    Click(48, 122)

    sleep(0.3)
    Click(455, 115)
    SendKeys("{Enter}")

    registro = WindowControl(Name="Registro de Salidas ")

    for intento in range(3):
        if registro.Exists(5):
            logger.info("Ventana Registro de Salidas encontrada")
            return registro
        else:
            logger.info(f"Intento {intento+1}: No se encontró la ventana")
            sleep(1)

    raise Exception("No se encontró la ventana 'Registro de Salidas'")


def abrir_registro_salida() -> WindowControl:
    registro = WindowControl(Name="Registro de Salidas ")
    registro.Exists(10)
    registro.ButtonControl(Name="CmdNew").Click()
    return registro


# =========================================================
# 🔹 CABECERA
# =========================================================


def debug_tabla_almacenes():
    tabla: TableControl = TableControl(Name="GrdCatalogo")

    if not tabla.Exists(5):
        raise Exception("❌ No se encontró la tabla de almacenes")

    logger.info("🔍 ===== INICIO DEBUG TABLA =====")

    filas = tabla.GetChildren()

    for i, fila in enumerate(filas):
        logger.info(f"\n🧾 FILA {i} → {fila.ControlTypeName}")

        grupos = fila.GetChildren()

        for j, grupo in enumerate(grupos):
            logger.info(f"   📦 GRUPO {j} → {grupo.ControlTypeName}")

            celdas = grupo.GetChildren()

            for k, celda in enumerate(celdas):
                texto = celda.Name.strip()
                logger.info(f"      🔹 Col {k}: '{texto}'")

    logger.info("\n🔍 ===== FIN DEBUG TABLA =====")


def seleccionar_almacen_destino_por_codigo(codigo_objetivo: str):
    codigo_objetivo = str(codigo_objetivo).strip()

    tabla_padre: TableControl = TableControl(Name="GrdCatalogo")
    tabla = tabla_padre.TableControl(Name="View 1")

    children = tabla.GetChildren()
    header = children[0]
    filas: list[CustomControl] = children[1:]
    # Lookin for code

    for fila in filas:
        code_data_item: DataItemControl = fila.DataItemControl(
            searchDepth=1, foundIndex=2, Name=""
        )
        xd = code_data_item.GetChildren()
        xdd = xd[0].GetChildren()
        text_edit: EditControl = code_data_item.EditControl(searchDepth=1, Name="Text1")
        codigo = text_edit.GetValuePattern().Value

        if codigo.strip() == codigo_objetivo:

            code_data_item.Click()  # más preciso
            return None

    raise Exception(f"❌ No se encontró el código: {codigo_objetivo}")


def rellenar_cabecera_salidas(registro: WindowControl, salidas: Salidas):

    sleep(1)
    # 🔹 Almacén origen (código)
    Click(780, 230)
    SendKeys(salidas.almacen_origen)
    SendKeys("{Enter}")

    sleep(0.3)

    # 🔹 Almacén destino (nombre)
    Click(1140, 230)
    sleep(2)  # 🔥 importante que cargue la tabla
    seleccionar_almacen_destino_por_codigo(salidas.almacen_destino)
    ButtonControl(Name="Aceptar").Click()
    sleep(0.3)

    # 🔹 Almacen virtual
    Click(780, 250)
    sleep(1)  # 🔥 espera que abra la ventana

    SendKeys(salidas.almacen_virtual_origen)
    sleep(1)

    # 🔥 buscar

    SendKeys("{Enter}")

    # 🔹 Concepto (combo)
    # seleccionar_combo_por_texto("cmbConcepto", salidas.concepto)
    # NOTE: Se tomo la decision de Harcodear ya que almenos se tiene entendido que siempre sera distribucion, ademas de que esta muy dificil poder seleccionar la acion ya que si jugamos con las opciones algunas quitan el almacen destino y a volver a querer poner distribucion nos da error
    sleep(1.5)
    Click(700, 280)
    sleep(1)
    Click(704, 340)
    sleep(1)
    Click(507, 307)
    sleep(1)
    sleep(1)
    Click(704, 340)
    sleep(1)
    Click(507, 307)
    sleep(1)


def procesar_salidas(
    salidas: tuple[Salidas, ...],
    fecha: str | None = None,
    fecha_fin: str | None = None,
    modo: str = "horario",
) -> dict:
    numero_procesado = obtener_siguiente_numero_procesado(fecha, fecha_fin, modo)
    total = len(salidas)
    ok_count = 0
    error_count = 0

    logger.info("[SALIDAS] Login SISMED...")
    login(SISMED_USERNAME, SISMED_PASSWORD)
    logger.info("[SALIDAS] Navegando a menu salidas...")
    sleep(2)
    navegar_a_salidas()

    for idx, salida in enumerate(salidas, start=1):

        verificar_backup_si_aplica()
        esperar_hora_backup_si_aplica()

        logger.info(
            f"[SALIDA {idx}/{total}] Procesando salida {salida.almacen_origen} -> {salida.almacen_destino} ({len(salida.medicamentos)} medicamentos)"
        )

        try:
            logger.debug(f"[SALIDA {idx}/{total}] Abriendo registro...")
            registro = abrir_registro_salida()

            logger.debug(f"[SALIDA {idx}/{total}] Rellenando cabecera...")
            rellenar_cabecera_salidas(registro, salida)

            logger.debug(
                f"[SALIDA {idx}/{total}] Agregando {len(salida.medicamentos)} productos..."
            )
            for producto in salida.medicamentos:
                agregar_producto(producto)

            logger.debug(f"[SALIDA {idx}/{total}] Guardando...")
            guardar()
            sleep(1)

            correlativo = extraer_correlativo_almacen()
            logger.debug(f"[SALIDA {idx}/{total}] Correlativo obtenido: {correlativo}")

            if salida.update_key:
                logger.debug(f"[SALIDA {idx}/{total}] Actualizando estado BD (00)...")
                ejecutar_sp_update_estado(salida.update_key, "00")

            row = crear_row_salida(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=salida.correlativo_ksalud,
                correlativo_sismed=correlativo,
                salida=salida,
                estado="OK",
            )

            logger.success(f"[SALIDA {idx}/{total}] OK -> correlativo={correlativo}")
            ok_count += 1

        except Exception as e:
            logger.exception(f"[SALIDA {idx}/{total}] Error: {e}")
            error_count += 1

            if salida.update_key:
                try:
                    ejecutar_sp_update_estado(salida.update_key, "20")
                except Exception as update_err:
                    logger.warning(
                        f"[SALIDA {idx}/{total}] No se pudo actualizar estado BD: {update_err}"
                    )

            close_doc_windows()

            row = crear_row_salida(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=salida.correlativo_ksalud,
                correlativo_sismed="",
                salida=salida,
                estado="ERROR",
                error=str(e),
            )

        cerrar_ventana_salida_guardada()
        sleep(1.5)
        SendKeys("{Enter}")

        guardar_movimientos(row, fecha, fecha_fin, modo)
        numero_procesado += 1

    logger.info("[SALIDAS] Cerrando SISMED...")
    cerrar_sismed()

    return {"total": total, "ok": ok_count, "error": error_count}


# =========================================================
# 🔹 AGREGAR PRODUCTO (CON SELECCIÓN DE LOTE)
# =========================================================


def _esperar_ventana_salida_producto() -> WindowControl:
    ventana = auto.WindowControl(ClassName="almacen7c000000")
    if ventana.Exists(maxSearchSeconds=5):
        logger.debug("[SALIDA PRODUCTO] Ventana encontrada por ClassName")
        return ventana

    ventana = auto.WindowControl(RegexName="Medicamentos e Insumos del Almacen")
    if ventana.Exists(maxSearchSeconds=3):
        logger.debug("[SALIDA PRODUCTO] Ventana encontrada por RegexName")
        return ventana

    raise RuntimeError("No se encontró la ventana de medicamentos para salida")


def _click_header_tabla(
    ventana: WindowControl, tabla_name: str, header_name: str
) -> None:
    tabla = ventana.TableControl(Name=tabla_name)
    if not tabla.Exists(maxSearchSeconds=3):
        raise RuntimeError(f"No se encontró la tabla '{tabla_name}'")

    view = tabla.TableControl(Name="View 1")
    if not view.Exists(maxSearchSeconds=3):
        raise RuntimeError(f"No se encontró 'View 1' dentro de '{tabla_name}'")

    header = view.HeaderControl(Name=header_name)
    if not header.Exists(maxSearchSeconds=3):
        raise RuntimeError(f"No se encontró el header '{header_name}'")

    header.Click()
    logger.debug(f"[SALIDA PRODUCTO] Click en header '{header_name}' de '{tabla_name}'")


def _leer_texto_celda(celda) -> str:
    # Si la celda contiene un EditControl, leer su Value pattern
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


def _parsear_stock(valor: str) -> int:
    if not valor:
        return 0
    valor = valor.replace(",", "").replace(".", "")
    try:
        return int(float(valor))
    except ValueError:
        return 0


def _seleccionar_lote(
    ventana: WindowControl, lote_esperado: str, cantidad: int
) -> None:
    if not lote_esperado:
        logger.warning("[SALIDA PRODUCTO] No se especificó lote, se usará primera fila")

    tabla = ventana.TableControl(Name="grdDetallado")
    if not tabla.Exists(maxSearchSeconds=3):
        raise RuntimeError("No se encontró la tabla 'grdDetallado'")

    view = tabla.TableControl(Name="View 1")
    if not view.Exists(maxSearchSeconds=3):
        raise RuntimeError("No se encontró 'View 1' dentro de 'grdDetallado'")

    filas = []
    for hijo in view.GetChildren():
        if "Group" in str(hijo.ControlType):
            continue
        filas.append(hijo)

    logger.debug(f"[SALIDA PRODUCTO] Filas de lotes encontradas: {len(filas)}")

    primera_fila = None
    for fila in filas:
        celdas = fila.GetChildren()
        if len(celdas) < 5:
            logger.debug(f"[SALIDA PRODUCTO] Fila ignorada, solo {len(celdas)} celdas")
            continue

        lote_valor = _leer_texto_celda(celdas[3])
        stock_valor = _parsear_stock(_leer_texto_celda(celdas[4]))

        logger.debug(f"[SALIDA PRODUCTO] Fila: lote='{lote_valor}' stock={stock_valor}")

        # Saltar fila de header si aparece como row
        if lote_valor in ("Lote", "", "Text1"):
            continue

        if primera_fila is None:
            primera_fila = fila

        if lote_esperado and lote_valor.strip() == lote_esperado.strip():
            if stock_valor < cantidad:
                raise RuntimeError(
                    f"Stock insuficiente para lote '{lote_esperado}': {stock_valor} < {cantidad}"
                )
            fila.Click()
            logger.info(
                f"[SALIDA PRODUCTO] Lote seleccionado: '{lote_esperado}' (stock: {stock_valor})"
            )
            return

    if lote_esperado and primera_fila:
        logger.warning(
            f"[SALIDA PRODUCTO] Lote '{lote_esperado}' no encontrado, usando primera fila"
        )
        primera_fila.Click()
        return

    if not primera_fila:
        raise RuntimeError("No se encontró ninguna fila de lotes")

    primera_fila.Click()


def agregar_producto(producto: Medicamento):
    logger.debug(
        f"[SALIDA PRODUCTO] Agregando código={producto.codigo}, lote={producto.lote}, cantidad={producto.cantidad}"
    )

    SendKeys("{CONTROL}{INSERT}")
    sleep(2)

    ventana = _esperar_ventana_salida_producto()

    _click_header_tabla(ventana, "GrdConsolidado", "Código")
    sleep(0.5)

    txt_buscar = ventana.EditControl(Name="txtBuscar")
    if not txt_buscar.Exists(maxSearchSeconds=3):
        raise RuntimeError("No se encontró el input 'txtBuscar'")

    escribir_input(txt_buscar, producto.codigo)
    sleep(0.3)

    btn_buscar = ventana.ButtonControl(Name="cmdBuscar")
    if not btn_buscar.Exists(maxSearchSeconds=3):
        raise RuntimeError("No se encontró el botón 'cmdBuscar'")
    btn_buscar.Click()
    logger.debug("[SALIDA PRODUCTO] Click en cmdBuscar")
    sleep(2)

    _seleccionar_lote(ventana, producto.lote, producto.cantidad)

    btn_aceptar = ventana.ButtonControl(Name="Aceptar")
    if not btn_aceptar.Exists(maxSearchSeconds=3):
        raise RuntimeError("No se encontró el botón 'Aceptar'")
    btn_aceptar.Click()
    logger.debug("[SALIDA PRODUCTO] Click en Aceptar")
    sleep(1.5)

    auto.SendKeys(str(producto.cantidad))
    sleep(0.5)

    registro = WindowControl(Name="Registro de Salidas ")
    if registro.Exists(maxSearchSeconds=3):
        btn_cmd_aceptar = registro.ButtonControl(Name="cmdAceptar")
        if btn_cmd_aceptar.Exists(maxSearchSeconds=2):
            btn_cmd_aceptar.Click()
            logger.debug("[SALIDA PRODUCTO] Click en cmdAceptar")
            sleep(0.5)
        else:
            logger.warning(
                "[SALIDA PRODUCTO] No se encontró cmdAceptar en Registro de Salidas"
            )
    else:
        logger.warning(
            "[SALIDA PRODUCTO] No se encontró ventana Registro de Salidas para cmdAceptar"
        )

    logger.success(
        f"[SALIDA PRODUCTO] Producto agregado: {producto.codigo} lote={producto.lote} cantidad={producto.cantidad}"
    )



