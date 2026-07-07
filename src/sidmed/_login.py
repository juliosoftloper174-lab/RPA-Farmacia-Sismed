from datetime import datetime
from subprocess import Popen
from time import sleep

from uiautomation import SendKeys, WindowControl, ButtonControl
from loguru import logger
from src import config
from src.notifications.email_sender import (
    enviar_correo,
    construir_cuerpo_backup,
)

_backup_pause_handled = False


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


def verificar_backup_si_aplica() -> None:
    backup = WindowControl(searchDepth=1, RegexName="Backups Automátic[o]?")
    regeneracion = WindowControl(searchDepth=1, RegexName="Regeneración de índices.*")
    if backup.Exists(maxSearchSeconds=0) or regeneracion.Exists(maxSearchSeconds=0):
        logger.warning("Ventana de backup/regeneración detectada durante procesamiento. Esperando...")
        _esperar_backup_automatico()


def esperar_hora_backup_si_aplica() -> None:
    global _backup_pause_handled
    if _backup_pause_handled:
        return

    ahora = datetime.now()
    hora_pausa_str = config.HORA_CIERRE
    hora_pausa = datetime.strptime(hora_pausa_str, "%H:%M").time()

    if ahora.time() >= hora_pausa:
        _backup_pause_handled = True
        logger.warning("=" * 60)
        logger.warning(f"HORA DE BACKUP ({hora_pausa_str}) ALCANZADA.")
        logger.warning("El bot se pausará para que realice el backup manual de SISMED.")
        logger.warning("Por favor:")
        logger.warning("  1. Realice el backup manual de SISMED")
        logger.warning("  2. Cierre TODAS las ventanas de SISMED")
        logger.warning("  3. Vuelva a esta terminal y presione Enter para continuar")
        logger.warning("=" * 60)

        if config.NOTIFICAR_CORREO:
            desc = f"<tr><td style='padding:4px 8px;font-weight:bold;'>Descripción:</td><td style='padding:4px 8px;'>{config.DESCRIPCION}</td></tr>" if config.DESCRIPCION else ""
            enviar_correo(
                f"🟡 Bot N°{config.BOT_NUMBER} - PAUSA PROGRAMADA (ventana de backup)",
                f"<html><body style='font-family:Arial,sans-serif;'>"
                f"<h2 style='color:#e67e22;'>🟡 PAUSA PROGRAMADA</h2>"
                f"<table style='border-collapse:collapse;width:100%;max-width:400px;'>"
                f"<tr><td style='padding:4px 8px;font-weight:bold;'>Hora:</td><td style='padding:4px 8px;'>{ahora.strftime('%H:%M:%S')}</td></tr>{desc}</table>"
                f"<p>El bot se ha pausado a las {ahora.strftime('%H:%M:%S')} porque se alcanzó la hora programada de backup ({hora_pausa_str}).</p>"
                f"<p>Esperando confirmación del operador para reanudar...</p>"
                f"<hr><p style='font-size:12px;color:#999;'>SISMED RPA Bot</p></body></html>",
            )

        input()

        logger.info("Reanudando procesamiento después de backup...")
        sleep(2)

        if config.NOTIFICAR_CORREO:
            desc = f"<tr><td style='padding:4px 8px;font-weight:bold;'>Descripción:</td><td style='padding:4px 8px;'>{config.DESCRIPCION}</td></tr>" if config.DESCRIPCION else ""
            enviar_correo(
                f"🟢 Bot N°{config.BOT_NUMBER} - REANUDADO (backup completado)",
                f"<html><body style='font-family:Arial,sans-serif;'>"
                f"<h2 style='color:#27ae60;'>🟢 REANUDADO</h2>"
                f"<table style='border-collapse:collapse;width:100%;max-width:400px;'>"
                f"<tr><td style='padding:4px 8px;font-weight:bold;'>Hora:</td><td style='padding:4px 8px;'>{datetime.now().strftime('%H:%M:%S')}</td></tr>{desc}</table>"
                f"<p>El bot se ha reanudado después del backup a las {datetime.now().strftime('%H:%M:%S')}.</p>"
                f"<p>Continuando con el procesamiento de movimientos.</p>"
                f"<hr><p style='font-size:12px;color:#999;'>SISMED RPA Bot</p></body></html>",
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
