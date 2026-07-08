from time import sleep

import uiautomation as auto

from src.helpers.comun.input import escribir_input
from src.logger import logger
from src.models.cliente import Cliente

SEXO_MAP = {
    "FEMENINO": "Femenino",
    "MASCULINO": "Masculino",
}

TIPO_DOCUMENTO_MAP = {
    "D.N.I": "LIBRETA ELECTORAL O  DNI",
    "CARNE DE EXTRANJERIA": "CARNET DE EXTRANJERIA",
    "RUC": "RUC",
    "PASAPORTE": "PASAPORTE",
}


def _normalizar_tipo_doc(raw: str) -> str:
    return raw.strip(" .").upper()


def _seleccionar_item_combo(combo, valor: str):
    combo.Click()
    sleep(0.5)
    auto.SendKeys("{Alt}{Down}")
    sleep(1)
    children = combo.GetChildren()
    for child in children:
        if child.Name.strip() == valor:
            child.Click()
            return
    logger.warning(f"No se encontró item '{valor}' en combo, escribiendo directamente")
    combo.SendKeys(valor)
    sleep(0.5)
    auto.SendKeys("{Enter}")


def registrar_cliente_en_sismed(cliente: Cliente) -> bool:
    logger.info(f"Abriendo modal de registro para cliente DNI={cliente.codigo}")

    ventana = auto.WindowControl(Name="Registro de Pedido")
    btn_nuevo = ventana.ButtonControl(Name="cmdNueCli")
    btn_nuevo.Click()

    modal = None
    for _ in range(20):
        modal = auto.WindowControl(Name="Registro de Nuevo Cliente")
        if modal.Exists(maxSearchSeconds=0.5):
            break
        sleep(0.5)
    else:
        logger.error("No apareció la ventana 'Registro de Nuevo Cliente' tras 10s")
        return False

    logger.info(f"Escribiendo nombre: {cliente.nombre}")
    txt_nombre = modal.EditControl(Name="TxtCLIDES")
    escribir_input(txt_nombre, cliente.nombre)

    if cliente.tipo_documento:
        logger.info(f"Seleccionando tipo documento: {cliente.tipo_documento}")
        tipo_normalizado = _normalizar_tipo_doc(cliente.tipo_documento)
        valor_combo = TIPO_DOCUMENTO_MAP.get(tipo_normalizado)
        if not valor_combo:
            logger.warning(
                f"Tipo documento no mapeado: '{cliente.tipo_documento}' (normalizado: '{tipo_normalizado}'), "
                f"usando valor directo"
            )
            valor_combo = cliente.tipo_documento
        combo = modal.ComboBoxControl(Name="cmbTDoc")
        _seleccionar_item_combo(combo, valor_combo)

    if cliente.sexo:
        logger.info(f"Seleccionando sexo: {cliente.sexo}")
        sexo_normalizado = cliente.sexo.strip().upper()
        nombre_radio = SEXO_MAP.get(sexo_normalizado)
        if not nombre_radio:
            logger.warning(f"Sexo no mapeado: '{cliente.sexo}', usando valor directo")
            nombre_radio = sexo_normalizado.capitalize()
        grupo = modal.GroupControl(Name="optsexo")
        radio = grupo.RadioButtonControl(Name=nombre_radio)
        radio.Click()
        logger.info(f"Sexo seleccionado: {nombre_radio}")

    if cliente.fecha_nacimiento:
        logger.info(f"Escribiendo fecha nacimiento: {cliente.fecha_nacimiento}")
        partes = cliente.fecha_nacimiento.split("-")
        fecha_formateada = f"{partes[2]}/{partes[1]}/{partes[0]}"
        logger.debug(f"Fecha formateada: {fecha_formateada}")
        fecha = modal.EditControl(Name="fechanac")
        fecha.Click()
        sleep(0.3)
        auto.SendKeys("{CONTROL}a")
        sleep(0.3)
        auto.SendKeys("{CONTROL}a")
        sleep(0.3)
        auto.SendKeys("{DEL}")
        sleep(0.3)
        fecha.SendKeys(fecha_formateada)
        logger.info(f"Fecha nacimiento escrita: {fecha_formateada}")

    logger.info(f"Escribiendo DNI: {cliente.codigo}")
    txt_dni = modal.EditControl(Name="TxtCLINUMEDOC")
    escribir_input(txt_dni, cliente.codigo)

    logger.info("Registro completado (modo prueba). Esperando 20s...")
    sleep(20)

    return True
