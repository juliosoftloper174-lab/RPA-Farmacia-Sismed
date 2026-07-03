import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from loguru import logger

from src import config


def _limpiar_password(password: str) -> str:
    return password.replace(" ", "")


def _fila_descripcion() -> str:
    if not config.DESCRIPCION:
        return ""
    return f"""
            <tr><td style="padding:4px 8px;font-weight:bold;">Descripción:</td><td style="padding:4px 8px;">{config.DESCRIPCION}</td></tr>"""


def enviar_correo(asunto: str, cuerpo_html: str) -> bool:
    if not config.NOTIFICAR_CORREO:
        logger.debug(f"[EMAIL] NOTIFICAR_CORREO=false, omitiendo: {asunto}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = config.SMTP_EMAIL
        msg["To"] = config.SMTP_DESTINO
        msg["Subject"] = asunto

        msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

        password = _limpiar_password(config.SMTP_PASSWORD)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(config.SMTP_EMAIL, password)
            server.send_message(msg)

        logger.success(f"[EMAIL] Enviado: {asunto}")
        return True

    except Exception as e:
        logger.warning(f"[EMAIL] No se pudo enviar correo ({asunto}): {e}")
        return False


def _tabla_resumen(stats: dict) -> str:
    filas = ""
    for label, valor in [
        ("Ingresos", stats.get("ingresos")),
        ("Salidas", stats.get("salidas")),
        ("Pedidos", stats.get("pedidos")),
    ]:
        if valor is None:
            continue
        t = valor["total"]
        ok = valor["ok"]
        err = valor["error"]
        sin_cliente = valor.get("sin_cliente", 0)
        partes = [f"{ok}/{t} OK", f"{err} error"]
        if sin_cliente:
            partes.append(f"{sin_cliente} s/cliente")
        filas += f"<tr><td>{label}</td><td>{' | '.join(partes)}</td></tr>\n"

    return filas


def _tabla_datos_sp(datos_sp: dict | None = None) -> str:
    if not datos_sp:
        return ""
    filas = ""
    for label, key in [("Ingresos", "ingresos"), ("Salidas", "salidas"), ("Pedidos", "pedidos")]:
        val = datos_sp.get(key, 0)
        filas += f"<tr><td style='padding:4px 32px;'>{label}:</td><td style='padding:4px 8px;'><strong>{val}</strong></td></tr>\n"
    return f"""
        <h3>📊 Datos capturados del SP</h3>
        <table style="border-collapse:collapse;width:100%;max-width:400px;">
            {filas}
        </table>"""


def construir_cuerpo_resumen(stats: dict) -> str:
    bot = config.BOT_NUMBER
    inicio = stats.get("hora_inicio", "")
    fin = stats.get("hora_fin", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    pendientes = stats.get("pendientes_otros", 0)
    desc = _fila_descripcion()

    tabla = _tabla_resumen(stats)

    pendientes_html = ""
    if pendientes:
        pendientes_html = f"""
        <h3 style="color:#e67e22;">📋 Pendientes</h3>
        <p>OTROS INGRESOS/EGRESOS: <strong>{pendientes}</strong> movimiento(s) pendiente(s) de implementación</p>
        """

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;color:#333;">
        <h2 style="color:#2c3e50;">✅ Bot N°{bot} — PROCESO FINALIZADO</h2>
        <table style="border-collapse:collapse;width:100%;max-width:500px;">
            <tr><td style="padding:4px 8px;font-weight:bold;">Hora inicio:</td><td style="padding:4px 8px;">{inicio}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;">Hora fin:</td><td style="padding:4px 8px;">{fin}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;">Bot número:</td><td style="padding:4px 8px;">{bot}</td></tr>{desc}
        </table>
        <h3>📊 Resumen</h3>
        <table style="border-collapse:collapse;width:100%;max-width:500px;border:1px solid #ddd;">
            <tr style="background:#3498db;color:white;"><th style="padding:8px;text-align:left;">Movimiento</th><th style="padding:8px;text-align:left;">Resultado</th></tr>
            {tabla}
        </table>
        {pendientes_html}
        <hr style="margin-top:20px;border:1px solid #eee;">
        <p style="font-size:12px;color:#999;">Correo enviado automáticamente por SISMED RPA Bot</p>
    </body>
    </html>
    """


def construir_cuerpo_backup(tipo: str) -> str:
    bot = config.BOT_NUMBER
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    desc = _fila_descripcion()

    if tipo == "inicio":
        titulo = "⚠️ BACKUP DETECTADO"
        mensaje = "El bot ha detectado el backup diario y está pausando operaciones."
        color = "#e67e22"
    else:
        titulo = "✅ BACKUP FINALIZADO"
        mensaje = "El backup diario ha finalizado. El bot reanuda operaciones."
        color = "#27ae60"

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;color:#333;">
        <h2 style="color:{color};">{titulo}</h2>
        <table style="border-collapse:collapse;width:100%;max-width:400px;">
            <tr><td style="padding:4px 8px;font-weight:bold;">Bot número:</td><td style="padding:4px 8px;">{bot}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;">Hora:</td><td style="padding:4px 8px;">{ahora}</td></tr>{desc}
        </table>
        <p>{mensaje}</p>
        <hr style="margin-top:20px;border:1px solid #eee;">
        <p style="font-size:12px;color:#999;">Correo enviado automáticamente por SISMED RPA Bot</p>
    </body>
    </html>
    """


def construir_cuerpo_inicio(datos_sp: dict | None = None) -> str:
    bot = config.BOT_NUMBER
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    desc = _fila_descripcion()
    sp = _tabla_datos_sp(datos_sp)

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;color:#333;">
        <h2 style="color:#2c3e50;">🟢 Bot N°{bot} — INICIADO</h2>
        <table style="border-collapse:collapse;width:100%;max-width:400px;">
            <tr><td style="padding:4px 8px;font-weight:bold;">Hora:</td><td style="padding:4px 8px;">{ahora}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;">Bot número:</td><td style="padding:4px 8px;">{bot}</td></tr>{desc}
        </table>
        <p>El bot ha comenzado a procesar movimientos.</p>
        {sp}
        <hr style="margin-top:20px;border:1px solid #eee;">
        <p style="font-size:12px;color:#999;">Correo enviado automáticamente por SISMED RPA Bot</p>
    </body>
    </html>
    """


def construir_cuerpo_reinicio() -> str:
    bot = config.BOT_NUMBER
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    desc = _fila_descripcion()

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;color:#333;">
        <h2 style="color:#e67e22;">🔄 Bot N°{bot} — REINICIADO TRAS CAÍDA</h2>
        <table style="border-collapse:collapse;width:100%;max-width:400px;">
            <tr><td style="padding:4px 8px;font-weight:bold;">Hora reinicio:</td><td style="padding:4px 8px;">{ahora}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;">Bot número:</td><td style="padding:4px 8px;">{bot}</td></tr>{desc}
        </table>
        <p>La ejecución anterior se interrumpió inesperadamente. El bot se ha reiniciado y continuará procesando.</p>
        <hr style="margin-top:20px;border:1px solid #eee;">
        <p style="font-size:12px;color:#999;">Correo enviado automáticamente por SISMED RPA Bot</p>
    </body>
    </html>
    """


def construir_cuerpo_error(error_msg: str) -> str:
    bot = config.BOT_NUMBER
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    desc = _fila_descripcion()

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;color:#333;">
        <h2 style="color:#e74c3c;">❌ Bot N°{bot} — ERROR CRÍTICO</h2>
        <table style="border-collapse:collapse;width:100%;max-width:500px;">
            <tr><td style="padding:4px 8px;font-weight:bold;">Hora:</td><td style="padding:4px 8px;">{ahora}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;">Bot número:</td><td style="padding:4px 8px;">{bot}</td></tr>{desc}
        </table>
        <h3 style="color:#e74c3c;">Detalle del error:</h3>
        <pre style="background:#fdf2f2;padding:12px;border-left:4px solid #e74c3c;white-space:pre-wrap;">{error_msg}</pre>
        <hr style="margin-top:20px;border:1px solid #eee;">
        <p style="font-size:12px;color:#999;">Correo enviado automáticamente por SISMED RPA Bot</p>
    </body>
    </html>
    """
