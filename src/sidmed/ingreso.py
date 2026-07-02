from datetime import datetime
from time import sleep

from uiautomation import (
    ButtonControl,
    Click,
    SendKeys,
    WindowControl,
)

from src.helpers.manejo_errores import cerrar_ventana_segura
from ..helpers.selecionar import seleccionar_combo_por_texto
from ..helpers.selecionar import seleccionar_combo_por_texto_con_autoenter
from ..config import SISMED_PASSWORD, SISMED_USERNAME

from src.models.ingreso import Ingreso
from src.models.Medicamento import Medicamento
from src.sidmed._login import login
from database.conexion import ejecutar_sp_update_estado
from src.sidmed._comun_almacen import (
    cerrar_sismed,
    cerrar_ventana_registro,
    close_doc_windows,
    extraer_correlativo_almacen,
    guardar,
)
from src.logger import logger
from src.reportes.excel_schema import crear_row_ingreso
from src.reportes.excel_writer import (
    guardar_movimientos,
    obtener_siguiente_numero_procesado,
)

# =========================================================
# 🔹 HELPERS
# =========================================================


def generar_codigo_ngr() -> str:
    return datetime.now().strftime("%Y%m%d%H%M")


# =========================================================
# 🔹 FLUJO BASE
# =========================================================


def navegar_a_ingresos():
    SendKeys("{Enter}")
    sleep(1)
    # quiero mandarle hacia abajo para que se posicione en ingresos
    SendKeys("{DOWN}")
    sleep(1)
    SendKeys("{DOWN}")
    sleep(1)
    SendKeys("{ENTER}")
    sleep(1)
    Click(360, 100)
    sleep(1)
    SendKeys("{Enter}")


def abrir_registro() -> WindowControl:

    registro = WindowControl(Name="Registro de Ingresos .")
    registro.Exists(10)

    registro.ButtonControl(Name="CmdNew").Click()
    return registro


def rellenar_ups(codigo_ups: str) -> None:
    # Abrir modal UPS (click ciego)
    sleep(1)
    Click(750, 380)
    sleep(1)

    # Escribir código
    # SendKeys(codigo_ups)
    SendKeys(
        "000"
    )  # NOTE: por ahora se asume que siempre se ingresa el ups 000 que significa sin ups
    sleep(1)

    # Botón aceptar
    # registro_pedido_window: WindowControl = FARMACIA_PANEL.WindowControl(searchDepth=1, Name="Registro de Pedido")
    # aceptar: ButtonControl = registro_pedido_window.ButtonControl(Name="Aceptar")
    aceptar: ButtonControl = ButtonControl(Name="Aceptar")
    aceptar.Click()


# =========================================================
# 🔹 CABECERA
# =========================================================


def rellenar_cabecera(registro: WindowControl, ingreso: Ingreso):

    Click(700, 230)
    sleep(1.8)
    # SendKeys(ingreso.almacen_origen)
    SendKeys("ALM. ANEXO RIOJA - SAN MARTIN")
    sleep(1.8)
    SendKeys("{Enter}{Enter}")

    sleep(2)
    Click(1140, 230)
    sleep(1)
    SendKeys(ingreso.almacen_destino)
    sleep(1)
    SendKeys("{Enter}")
    # NOTE: aqui se rellena el almacen virtual, esto no lee la base de datos, se asume que siempre sera el primero, se puede mejorar este apartado, por ahora trabajemoslo asi
    sleep(1.8)
    Click(775, 255)
    sleep(1.8)
    SendKeys(ingreso.almacen_virtual_origen)
    sleep(1.8)
    SendKeys("{Enter}")
    sleep(1.5)

    seleccionar_combo_por_texto_con_autoenter("cmbConcepto", ingreso.concepto)

    codigo = generar_codigo_ngr()
    registro.EditControl(Name="txtGuiaRemision").SendKeys(codigo)

    rellenar_ups("000")


# =========================================================
# 🔹 PRODUCTOS
# =========================================================


def abrir_modal():

    sleep(0.5)
    SendKeys("{CONTROL}{INSERT}")
    sleep(5)


def limpiar_y_escribir(edit, valor):

    # foco real
    edit.Click()
    sleep(0.5)

    # seleccionar todo
    SendKeys("{CONTROL}a")
    sleep(0.3)

    # borrar
    SendKeys("{DEL}")
    sleep(0.3)

    # escribir nuevo valor
    edit.SendKeys(str(valor))
    sleep(0.5)


def limpiar_registro_sanitario(edit, valor):

    edit.Click()
    sleep(0.5)

    # borrar contenido actual
    for _ in range(13):
        SendKeys("{BS}")
        sleep(0.05)

    sleep(0.3)

    # escribir nuevo valor
    edit.SendKeys(str(valor))
    sleep(0.5)


def formatear_fecha_sismed(fecha: str) -> str:
    """
    Convierte:
    2029/12/07

    a:
    07122029
    """

    anio, mes, dia = fecha.split("/")

    return f"{dia}{mes}{anio}"


def agregar_producto(registro: WindowControl, producto: Medicamento):

    # =====================================================
    # CODIGO
    # =====================================================

    registro.EditControl(Name="txtCodigo").SendKeys(producto.codigo)

    SendKeys("{Enter}")
    sleep(0.5)

    # =====================================================
    # LOTE
    # =====================================================

    registro.EditControl(Name="txtLote").SendKeys(producto.lote)

    SendKeys("{Enter}")
    sleep(1)

    # =====================================================
    # FECHA
    # =====================================================

    fecha_vencimiento_formato = formatear_fecha_sismed(producto.fecha_vencimiento)

    sleep(1)
    Click(810, 632)
    sleep(1)

    # escribir fecha completa:
    # DDMMYYYY
    SendKeys(fecha_vencimiento_formato)

    sleep(0.5)

    # =====================================================
    # REGISTRO SANITARIO
    # =====================================================

    # el contenido ya queda seleccionado automáticamente
    # pero por seguridad escribimos primero una letra
    SendKeys("a")

    sleep(0.5)

    # eliminamos todo el contenido seleccionado
    SendKeys("{BACK}")

    sleep(0.3)

    # escribimos el registro sanitario real
    registro.EditControl(Name="txtFabricante").SendKeys(producto.registro_sanitario)

    sleep(0.5)

    SendKeys("{Enter}")

    sleep(0.5)

    # =====================================================
    # TIPO DE SUMINISTRO
    # =====================================================

    seleccionar_combo_por_texto("cbotipsum", producto.tipo_sum)

    # =====================================================
    # FUENTE DE FINANCIAMIENTO
    # =====================================================

    seleccionar_combo_por_texto("cboffin", producto.fuente_fin)

    # =====================================================
    # CANTIDAD
    # =====================================================

    registro.EditControl(Name="txtCantidad").SendKeys(str(producto.cantidad))

    SendKeys("{Enter}")

    sleep(0.5)

    # =====================================================
    # TEMPERATURA
    # =====================================================

    # dejamos el valor por defecto
    SendKeys("{Enter}")

    sleep(0.5)

    # =====================================================
    # PRECIO
    # =====================================================

    registro.EditControl(Name="txtPrecio").SendKeys(str(producto.precio_compra))

    SendKeys("{Enter}")

    sleep(0.5)

    # =====================================================
    # ACEPTAR
    # =====================================================

    registro.ButtonControl(Name="cmdAceptar").Click()

    sleep(1)


def agregar_productos(registro: WindowControl, ingreso: Ingreso):
    for producto in ingreso.medicamentos:
        abrir_modal()
        agregar_producto(registro, producto)


# =========================================================
# 🔹 MAIN
# =========================================================


def procesar_ingresos(ingresos: tuple[Ingreso, ...]) -> dict:
    numero_procesado = obtener_siguiente_numero_procesado()
    total = len(ingresos)
    ok_count = 0
    error_count = 0

    logger.info("[INGRESOS] Login SISMED...")
    login(SISMED_USERNAME, SISMED_PASSWORD)
    logger.info("[INGRESOS] Navegando a menu ingresos...")
    sleep(2)
    navegar_a_ingresos()

    for idx, ingreso in enumerate(ingresos, start=1):

        logger.info(f"[INGRESO {idx}/{total}] Procesando ingreso a {ingreso.almacen_destino} ({len(ingreso.medicamentos)} medicamentos)")

        try:
            logger.debug(f"[INGRESO {idx}/{total}] Abriendo registro...")
            registro = abrir_registro()

            logger.debug(f"[INGRESO {idx}/{total}] Rellenando cabecera...")
            rellenar_cabecera(registro, ingreso)

            logger.debug(f"[INGRESO {idx}/{total}] Agregando {len(ingreso.medicamentos)} productos...")
            agregar_productos(registro, ingreso)

            logger.debug(f"[INGRESO {idx}/{total}] Guardando...")
            guardar()

            sleep(1)

            correlativo: str = extraer_correlativo_almacen()
            logger.debug(f"[INGRESO {idx}/{total}] Correlativo obtenido: {correlativo}")

            if ingreso.update_key:
                logger.debug(f"[INGRESO {idx}/{total}] Actualizando estado BD (00)...")
                ejecutar_sp_update_estado(ingreso.update_key, "00")

            row = crear_row_ingreso(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=ingreso.correlativo_ksalud,
                correlativo_sismed=correlativo,
                ingreso=ingreso,
                estado="OK",
            )

            logger.success(f"[INGRESO {idx}/{total}] OK -> correlativo={correlativo}")
            ok_count += 1

        except Exception as e:
            logger.exception(f"[INGRESO {idx}/{total}] Error: {e}")
            error_count += 1

            if ingreso.update_key:
                try:
                    ejecutar_sp_update_estado(ingreso.update_key, "10")
                except Exception as update_err:
                    logger.warning(f"[INGRESO {idx}/{total}] No se pudo actualizar estado BD: {update_err}")

            close_doc_windows()

            row = crear_row_ingreso(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=ingreso.correlativo_ksalud,
                correlativo_sismed="",
                ingreso=ingreso,
                estado="ERROR",
                error=str(e),
            )

        cerrar_ventana_registro()
        sleep(1.5)
        SendKeys("{Enter}")

        guardar_movimientos(row)
        numero_procesado += 1

    logger.info("[INGRESOS] Cerrando SISMED...")
    cerrar_sismed()

    return {"total": total, "ok": ok_count, "error": error_count}
