from subprocess import Popen
from time import sleep

from uiautomation import SendKeys, WindowControl, ButtonControl
from loguru import logger
from src import config
from src.notifications.email_sender import (
    enviar_correo,
    construir_cuerpo_backup,
)


def _verificar_backup_diario() -> None:
    backup_diario = WindowControl(
        searchDepth=1, RegexName="Envío de información de Consumo Diaria.*"
    )

    if not backup_diario.Exists(maxSearchSeconds=0):
        return

    logger.warning("=" * 60)
    logger.warning("VENTANA 'ENVÍO DE INFORMACIÓN DE CONSUMO DIARIA' DETECTADA")
    logger.warning("El backup diario está en proceso.")
    logger.warning(
        "Por favor:\n"
        "  1. Realice el backup manualmente\n"
        "  2. Cierre TODAS las ventanas de SISMED\n"
        "  3. Vuelva a esta terminal y presione Enter"
    )
    logger.warning("=" * 60)

    input()

    logger.info("Usuario confirmó backup completado. Reabriendo SISMED...")
    sleep(2)
    Popen(config.SISMED_EXE)
    sleep(3)


def _ignorar_program_error() -> None:
    # NOTE: no se sabe con seguridad si el boton se llama Ignore,
    # sera trabajo para despues
    error = WindowControl(Name="Program Error")
    if error.Exists(maxSearchSeconds=0):
        ignore = error.ButtonControl(searchDepth=1, Name="Ignore")
        if ignore.Exists():
            ignore.Click()
            logger.warning("Program Error ignorado durante backup.")


def _esperar_backup_automatico() -> None:
    backup = WindowControl(searchDepth=1, RegexName="Backups Automátic[o]?")
    if not backup.Exists(maxSearchSeconds=0):
        return

    logger.warning("Backup detectado. Esperando que finalice...")
    enviar_correo(
        f"⚠️ Bot N°{config.BOT_NUMBER} - BACKUP DETECTADO",
        construir_cuerpo_backup("inicio"),
    )

    for i in range(15):
        for _ in range(6):
            sleep(10)
            _ignorar_program_error()
        if not backup.Exists(maxSearchSeconds=0):
            logger.info("Backup finalizado.")
            break
        logger.warning(f"Backup en curso... ({i+1}/15, ~{i+1} min)")
    else:
        logger.critical("Backup no finalizó tras 15 min.")

    sleep(2)

    regeneracion = WindowControl(searchDepth=1, RegexName="Regeneración de índices.*")
    if regeneracion.Exists(maxSearchSeconds=0):
        logger.warning("Regeneración de índices detectada. Esperando...")
        for i in range(10):
            for _ in range(6):
                sleep(10)
                _ignorar_program_error()
            if not regeneracion.Exists(maxSearchSeconds=0):
                logger.info("Regeneración de índices finalizada.")
                break
            logger.warning(f"Regeneración en curso... ({i+1}/10)")

    enviar_correo(
        f"✅ Bot N°{config.BOT_NUMBER} - BACKUP FINALIZADO",
        construir_cuerpo_backup("fin"),
    )


def login(username: str, password: str) -> None:
    SendKeys("{Win}d")

    LOGIN_WINDOW = WindowControl(Name="Acceso al Sistema")
    if not LOGIN_WINDOW.Exists(maxSearchSeconds=0):
        Popen(config.SISMED_EXE)
        sleep(3)
        LOGIN_WINDOW = WindowControl(Name="Acceso al Sistema")

    _verificar_backup_diario()
    _esperar_backup_automatico()

    while True:
        try:
            LOGIN_WINDOW = WindowControl(Name="Acceso al Sistema")
            LOGIN_WINDOW.EditControl(Name="txtUsuario").SendKeys(username)
            LOGIN_WINDOW.EditControl(Name="txtClave").SendKeys(password)
            LOGIN_WINDOW.ButtonControl(Name="Aceptar").Click()

            return cerrar_ventana_inicial()

        except Exception as e:
            logger.error(f"No se pudo completar el login: {e}")
            logger.warning(
                "\n" + "=" * 60 + "\n"
                "  SISMED no pudo iniciar sesión automáticamente.\n"
                "  Verifique que SISMED esté accesible (sin ventanas bloqueando)\n"
                "  y presione Enter para reintentar...\n"
                + "=" * 60
            )
            input()
            Popen(config.SISMED_EXE)
            sleep(3)


def cerrar_ventana_inicial() -> None:
    ventana: WindowControl = WindowControl(Name="Productos Vencidos y por Vencer")
    if ventana.Exists():
        exit_button: ButtonControl = ventana.ButtonControl(Name="Salir")
        exit_button.Click()
    return None
