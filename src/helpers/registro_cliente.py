from time import sleep

from src.helpers.input import escribir_input
from src.helpers.windows import get_farmacia_window, get_registro_pedido_window
from src.logger import logger
from src.models.cliente import Cliente


def registrar_cliente_en_sismed(cliente: Cliente) -> bool:
    logger.info(f"Abriendo modal de registro para cliente DNI={cliente.codigo}")

    ventana = get_registro_pedido_window()
    btn_nuevo = ventana.ButtonControl(Name="cmdNueCli")
    btn_nuevo.Click()

    modal = None
    for _ in range(20):
        modal = get_farmacia_window().WindowControl(Name="Registro de Nuevo Cliente")
        if modal.Exists(maxSearchSeconds=0.5):
            break
        sleep(0.5)
    else:
        logger.error("No apareció la ventana 'Registro de Nuevo Cliente' tras 10s")
        return False

    logger.info(f"Escribiendo nombre: {cliente.nombre}")
    txt_nombre = modal.EditControl(Name="TxtCLIDES")
    escribir_input(txt_nombre, cliente.nombre)

    logger.info(f"Escribiendo DNI: {cliente.codigo}")
    txt_dni = modal.EditControl(Name="TxtCLINUMEDOC")
    escribir_input(txt_dni, cliente.codigo)

    logger.info("Registro completado (modo prueba). Esperando 20s...")
    sleep(20)

    return True
