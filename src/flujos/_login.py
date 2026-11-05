from datetime import datetime
from pathlib import Path
from subprocess import Popen
from time import sleep

from uiautomation import ButtonControl, EditControl, SendKeys, WindowControl
from loguru import logger
from src import config
from src.notifications.email_sender import (
    enviar_correo,
    enviar_correo_con_adjunto,
    construir_cuerpo_backup,
    construir_cuerpo_resumen_diario,
)
from src.reportes.excel_writer import leer_resumen_diario, _path_del_dia

_backup_pause_handled = False

# Timeouts (rama dos bots, SISMED en Z: responde lento)
LOGIN_ESPERA_INICIAL = 8
LOGIN_ESPERA_VENTANA = 20
LOGIN_TIMEOUT_CONTROLES = 15
LOGIN_MAX_INTENTOS = 3
LOGIN_ESPERA_REINTENTO = 5

PATRONES_BACKUP = [
    "Envío de información de Consumo Diaria.*",
    "Backups Automátic[o]?",
    "Regeneración de índices.*",
]


def _pausar_por_backup() -> bool:
    for patron in PATRONES_BACKUP:
        ventana = WindowControl(searchDepth=1, RegexName=patron)
        if not ventana.Exists(maxSearchSeconds=0):
            continue

        logger.warning("=" * 60)
        logger.warning(f"BACKUP DETECTADO — ventana: {patron}")
        logger.warning(
            "El bot se pausa. Realice el backup manualmente,\n"
            "cierre TODAS las ventanas de SISMED y presione Enter."
        )
        logger.warning("=" * 60)

        enviar_correo(
            f"⚠️ Bot N°{config.BOT_NUMBER} - BACKUP DETECTADO",
            construir_cuerpo_backup("inicio"),
        )

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        resumen = leer_resumen_diario(fecha_hoy)
        excel_path = _path_del_dia(fecha_hoy)
        enviar_correo_con_adjunto(
            f"📊 Bot N°{config.BOT_NUMBER} - Resumen parcial (backup detectado)",
            construir_cuerpo_resumen_diario(resumen, fecha_hoy),
            excel_path,
        )

        input()
        sleep(1)

        logger.info("Backup confirmado. Reanudando...")
        enviar_correo(
            f"✅ Bot N°{config.BOT_NUMBER} - BACKUP FINALIZADO",
            construir_cuerpo_backup("fin"),
        )
        return True

    return False


def verificar_backup_si_aplica() -> None:
    _pausar_por_backup()


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

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        resumen = leer_resumen_diario(fecha_hoy)
        excel_path = _path_del_dia(fecha_hoy)
        enviar_correo_con_adjunto(
            f"📊 Bot N°{config.BOT_NUMBER} - Resumen pre-backup ({config.HORA_CIERRE})",
            construir_cuerpo_resumen_diario(resumen, fecha_hoy),
            excel_path,
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


def _abrir_sismed() -> None:
    exe = Path(config.SISMED_EXE)
    Popen(str(exe), cwd=str(exe.parent))


def _esperar_ventana_login(timeout: float) -> WindowControl | None:
    ventana = WindowControl(Name="Acceso al Sistema")
    if ventana.Exists(maxSearchSeconds=timeout, searchIntervalSeconds=0.5):
        return ventana
    return None


def _hay_proceso_sismed() -> bool:
    if WindowControl(Name="Acceso al Sistema").Exists(maxSearchSeconds=0):
        return True
    return WindowControl(
        searchDepth=1, RegexName=r"^(MINSA SISMED|FARMACIA - MINSA SISMED).*"
    ).Exists(maxSearchSeconds=0)


def login(username: str, password: str) -> None:
    SendKeys("{Win}d")

    for intento in range(1, LOGIN_MAX_INTENTOS + 1):
        espera = LOGIN_ESPERA_INICIAL if intento == 1 else LOGIN_ESPERA_VENTANA
        ventana = _esperar_ventana_login(espera)

        if ventana is None:
            logger.warning(
                f"[LOGIN] Ventana de acceso no encontrada "
                f"(intento {intento}/{LOGIN_MAX_INTENTOS}), abriendo SISMED..."
            )
            if not _hay_proceso_sismed():
                _abrir_sismed()
            sleep(LOGIN_ESPERA_REINTENTO)
            continue

        if _pausar_por_backup():
            ventana = _esperar_ventana_login(LOGIN_ESPERA_VENTANA)
            if ventana is None:
                continue

        try:
            usuario: EditControl = ventana.EditControl(Name="txtUsuario", searchDepth=2)
            if not usuario.Exists(
                maxSearchSeconds=LOGIN_TIMEOUT_CONTROLES,
                searchIntervalSeconds=0.5,
            ):
                raise RuntimeError("No apareció el campo 'txtUsuario'")

            clave: EditControl = ventana.EditControl(Name="txtClave", searchDepth=2)
            if not clave.Exists(
                maxSearchSeconds=LOGIN_TIMEOUT_CONTROLES,
                searchIntervalSeconds=0.5,
            ):
                raise RuntimeError("No apareció el campo 'txtClave'")

            aceptar: ButtonControl = ventana.ButtonControl(
                Name="Aceptar", searchDepth=2
            )
            if not aceptar.Exists(
                maxSearchSeconds=LOGIN_TIMEOUT_CONTROLES,
                searchIntervalSeconds=0.5,
            ):
                raise RuntimeError("No apareció el botón 'Aceptar'")

            usuario.SendKeys(username)
            clave.SendKeys(password)
            aceptar.Click()

            cerrar_ventana_inicial()
            return

        except Exception as e:
            logger.error(
                f"[LOGIN] No se pudo completar el login "
                f"(intento {intento}/{LOGIN_MAX_INTENTOS}): {e}"
            )
            sleep(LOGIN_ESPERA_REINTENTO)

            if not _hay_proceso_sismed():
                logger.warning("[LOGIN] SISMED no está abierto, lanzando de nuevo...")
                _abrir_sismed()
                sleep(LOGIN_ESPERA_VENTANA)

    raise RuntimeError(
        f"No se pudo iniciar sesión en SISMED tras {LOGIN_MAX_INTENTOS} intentos"
    )


def cerrar_ventana_inicial() -> None:
    ventana: WindowControl = WindowControl(Name="Productos Vencidos y por Vencer")
    if ventana.Exists(maxSearchSeconds=8, searchIntervalSeconds=0.5):
        exit_button: ButtonControl = ventana.ButtonControl(Name="Salir")
        if exit_button.Exists(maxSearchSeconds=5, searchIntervalSeconds=0.5):
            exit_button.Click()
    return None
