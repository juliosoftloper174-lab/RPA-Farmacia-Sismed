from time import sleep

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
from src.models.Medicamento import Medicamento
from src.models.Salidas import Salidas
from src.reportes.excel_schema import crear_row_salida
from src.reportes.excel_writer import (
    guardar_movimientos,
    obtener_siguiente_numero_procesado,
)
from src.flujos._comun_almacen import (
    cerrar_sismed,
    cerrar_ventana_salida_guardada,
    close_doc_windows,
    extraer_correlativo_almacen,
    guardar,
)

from src.config import SISMED_PASSWORD, SISMED_USERNAME
from src.logger import logger
from src.flujos._login import login, verificar_backup_si_aplica, esperar_hora_backup_si_aplica

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
    sleep(2)
    Click(700, 280)
    sleep(2)
    Click(704, 340)
    sleep(2)
    Click(507, 307)
    sleep(2)
    sleep(1)
    Click(704, 340)
    sleep(2)
    sleep(1)
    Click(507, 307)
    sleep(2)


def procesar_salidas(salidas: tuple[Salidas, ...], fecha: str | None = None, fecha_fin: str | None = None, modo: str = "horario") -> dict:
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


def agregar_producto(producto: Medicamento):

    # se iba a trabajar usando inspecto pero la ventana cambia de nombre segun el almacen virtual seleccionado, alm destino, almacen origen, etc, por lo que es muy dificil asegurar el nombre de la ventana, por lo que se decidio trabajar con clicks en coordenadas especificas, ya que se tiene entendido que la ventana siempre va a tener la misma estructura y los mismos campos en las mismas posiciones

    SendKeys("{CONTROL}{INSERT}")  # abre ventana de agregar producto
    sleep(3)
    Click(825, 355)  # clic en el campo de codigo
    sleep(3)
    Click(615, 315)  # clic en el txt busca
    sleep(3)
    SendKeys(producto.codigo)  # busca el producto
    sleep(3)
    SendKeys("{Enter}")
    sleep(3)
    SendKeys("{Enter}")  # selecciona el producto
    sleep(3)
    SendKeys("{Enter}")
    sleep(3)
    SendKeys(str(producto.cantidad))  # ingresa la cantidad
    sleep(3)
    SendKeys("{Enter}")
    SendKeys("{Enter}")
    pass
