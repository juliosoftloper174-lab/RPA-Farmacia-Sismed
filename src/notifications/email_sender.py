import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from pathlib import Path

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


def _fila_rango_fechas(fecha_ini: str | None = None, fecha_fin: str | None = None) -> str:
    if not fecha_ini or not fecha_fin:
        return ""
    return f"""
            <tr><td style="padding:4px 8px;font-weight:bold;">Rango fechas:</td><td style="padding:4px 8px;">{fecha_ini} → {fecha_fin}</td></tr>"""


def _pendientes_html(saltados: int) -> str:
    if not saltados:
        return ""
    return f"""
        <h3 style="color:#e67e22;">📋 Pendientes</h3>
        <p>OTROS INGRESOS/EGRESOS: <strong>{saltados}</strong> movimiento(s) pendiente(s) de implementación</p>"""






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





def construir_cuerpo_resumen_diario(resumen: dict, fecha: str) -> str:
    bot = config.BOT_NUMBER
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    desc = _fila_descripcion()

    filas = ""
    for label, key in [("Ingresos", "ingresos"), ("Salidas", "salidas"), ("Pedidos", "pedidos")]:
        total = resumen.get(key, 0)
        filas += f"<tr><td style='padding:4px 32px;'>{label}:</td><td style='padding:4px 8px;'><strong>{total}</strong></td></tr>\n"

    ok = resumen.get("ok", 0)
    error = resumen.get("error", 0)
    sin_stock = resumen.get("sin_stock", 0)
    saltados = resumen.get("saltados", 0)
    validacion = resumen.get("validacion", 0)

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;color:#333;">
        <h2 style="color:#2c3e50;">📅 Bot N°{bot} — RESUMEN DIARIO</h2>
        <table style="border-collapse:collapse;width:100%;max-width:400px;">
            <tr><td style="padding:4px 8px;font-weight:bold;">Fecha:</td><td style="padding:4px 8px;">{fecha}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;">Hora resumen:</td><td style="padding:4px 8px;">{ahora}</td></tr>{desc}
        </table>
        <h3>📊 Totales del dia</h3>
        <table style="border-collapse:collapse;width:100%;max-width:400px;">{filas}</table>
        <h3>✅ Resultados</h3>
        <table style="border-collapse:collapse;width:100%;max-width:400px;">
            <tr><td style="padding:4px 32px;">✅ OK:</td><td style="padding:4px 8px;"><strong>{ok}</strong></td></tr>
            <tr><td style="padding:4px 32px;">❌ Error:</td><td style="padding:4px 8px;"><strong>{error}</strong></td></tr>
            <tr><td style="padding:4px 32px;">⚠️ Sin stock:</td><td style="padding:4px 8px;"><strong>{sin_stock}</strong></td></tr>
            <tr><td style="padding:4px 32px;">⏭️ Saltados:</td><td style="padding:4px 8px;"><strong>{saltados}</strong></td></tr>
            <tr><td style="padding:4px 32px;">📋 Validación:</td><td style="padding:4px 8px;"><strong>{validacion}</strong></td></tr>
        </table>
        <hr style="margin-top:20px;border:1px solid #eee;">
        <p style="font-size:12px;color:#999;">Correo enviado automaticamente por SISMED RPA Bot</p>
    </body>
    </html>
    """


def enviar_correo_con_adjunto(asunto: str, cuerpo_html: str, ruta_adjunto: str | Path) -> bool:
    if not config.NOTIFICAR_CORREO:
        logger.debug(f"[EMAIL] NOTIFICAR_CORREO=false, omitiendo (con adjunto): {asunto}")
        return False

    try:
        msg = MIMEMultipart("mixed")
        msg["From"] = config.SMTP_EMAIL
        msg["To"] = config.SMTP_DESTINO
        msg["Subject"] = asunto

        msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

        adjunto = Path(ruta_adjunto)
        if adjunto.exists():
            with open(adjunto, "rb") as f:
                part = MIMEApplication(f.read(), Name=adjunto.name)
                part["Content-Disposition"] = f'attachment; filename="{adjunto.name}"'
                msg.attach(part)

        password = _limpiar_password(config.SMTP_PASSWORD)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(config.SMTP_EMAIL, password)
            server.send_message(msg)

        logger.success(f"[EMAIL] Enviado (con adjunto): {asunto}")
        return True

    except Exception as e:
        logger.warning(f"[EMAIL] No se pudo enviar correo con adjunto ({asunto}): {e}")
        return False
