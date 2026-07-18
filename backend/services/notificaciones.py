"""
Servicio de notificaciones externas para SIGPDA.
Envía email (Gmail SMTP) y/o WhatsApp (Twilio) en un hilo background,
leyendo la configuración directamente de la tabla `configuracion`.
"""

import logging
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from database.conexion import obtener_sesion
from database.modelos import Configuracion

logger = logging.getLogger(__name__)

_CLAVES = [
    "notif_email_activa",
    "notif_email_destino",
    "notif_email_remitente",
    "notif_email_password",
    "notif_whatsapp_activa",
    "notif_telefono",
    "notif_twilio_sid",
    "notif_twilio_token",
    "notif_twilio_numero",
]


def _leer_config() -> dict:
    sesion = obtener_sesion()
    try:
        rows = sesion.query(Configuracion).filter(Configuracion.clave.in_(_CLAVES)).all()
        return {r.clave: (r.valor or "").strip() for r in rows}
    finally:
        sesion.close()


def _html_alertas(alertas: list[dict]) -> str:
    total = len(alertas)
    criticas = sum(1 for a in alertas if a.get("nivel") == "CRITICO")
    altas = sum(1 for a in alertas if a.get("nivel") == "ALTO")

    colores = {"CRITICO": "#dc2626", "ALTO": "#ea580c", "MEDIO": "#d97706", "BAJO": "#16a34a"}
    filas = "".join(
        f"<tr>"
        f"<td style='padding:6px 10px;color:{colores.get(a.get('nivel',''), '#333')};font-weight:bold'>"
        f"{a.get('nivel','')}</td>"
        f"<td style='padding:6px 10px'>{a.get('tipo','')}</td>"
        f"</tr>"
        for a in alertas[:25]
    )

    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px">
      <h2 style="color:#6366f1">🔔 SIGPDA — Alertas Inteligentes</h2>
      <p>Se generaron <b>{total}</b> alerta(s) nueva(s):</p>
      <div style="display:flex;gap:12px;margin:12px 0">
        <span style="background:#fef2f2;color:#dc2626;padding:6px 14px;border-radius:8px;font-weight:bold">
          Críticas: {criticas}
        </span>
        <span style="background:#fff7ed;color:#ea580c;padding:6px 14px;border-radius:8px;font-weight:bold">
          Altas: {altas}
        </span>
        <span style="background:#f0fdf4;color:#16a34a;padding:6px 14px;border-radius:8px;font-weight:bold">
          Total: {total}
        </span>
      </div>
      <table style="border-collapse:collapse;width:100%;margin-top:12px">
        <thead>
          <tr style="background:#f3f4f6">
            <th style="padding:8px 10px;text-align:left">Nivel</th>
            <th style="padding:8px 10px;text-align:left">Tipo de alerta</th>
          </tr>
        </thead>
        <tbody>{filas}</tbody>
      </table>
      {"<p style='color:#6b7280;font-size:13px'>... y más alertas. Ingresa al sistema para el detalle completo.</p>" if total > 25 else ""}
      <p style="margin-top:20px;color:#6b7280;font-size:12px">
        Sistema SIGPDA — Gestión y Predicción de Desperdicio Alimentario
      </p>
    </div>
    """


def _enviar_email(cfg: dict, alertas: list[dict]) -> None:
    destino = cfg.get("notif_email_destino", "")
    remitente = cfg.get("notif_email_remitente", "")
    password = cfg.get("notif_email_password", "")
    if not (destino and remitente and password):
        logger.warning("Email de alertas no configurado — omitiendo envío")
        return

    total = len(alertas)
    criticas = sum(1 for a in alertas if a.get("nivel") == "CRITICO")
    asunto = f"SIGPDA — {total} alerta(s) nueva(s)" + (f" ({criticas} crítica(s))" if criticas else "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = f"SIGPDA <{remitente}>"
    msg["To"] = destino
    msg.attach(MIMEText(_html_alertas(alertas), "html", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(remitente, password)
            smtp.sendmail(remitente, destino, msg.as_string())
        logger.info(f"Notificación de alertas enviada por email a {destino}")
    except smtplib.SMTPAuthenticationError:
        logger.error("Email: credenciales incorrectas. Verifica remitente y contraseña de aplicación Gmail.")
    except Exception as exc:
        logger.error(f"Email: error al enviar — {exc}")


def _enviar_whatsapp(cfg: dict, alertas: list[dict]) -> None:
    telefono = cfg.get("notif_telefono", "")
    sid = cfg.get("notif_twilio_sid", "")
    token = cfg.get("notif_twilio_token", "")
    numero_twilio = cfg.get("notif_twilio_numero", "")
    if not (telefono and sid and token and numero_twilio):
        logger.warning("WhatsApp no configurado — omitiendo envío")
        return

    total = len(alertas)
    criticas = sum(1 for a in alertas if a.get("nivel") == "CRITICO")
    altas = sum(1 for a in alertas if a.get("nivel") == "ALTO")
    texto = (
        f"🔔 *SIGPDA — {total} alerta(s) nueva(s)*\n"
        f"🔴 Críticas: {criticas}  🟠 Altas: {altas}\n"
        f"Ingresa al sistema para ver el detalle completo."
    )

    try:
        from twilio.rest import Client  # pip install twilio
        client = Client(sid, token)
        client.messages.create(
            body=texto,
            from_=f"whatsapp:{numero_twilio}",
            to=f"whatsapp:{telefono}",
        )
        logger.info(f"Notificación WhatsApp enviada a {telefono}")
    except ImportError:
        logger.warning("Twilio no instalado. Ejecuta: pip install twilio")
    except Exception as exc:
        logger.error(f"WhatsApp: error al enviar — {exc}")


def enviar_notificaciones(alertas_creadas: list[dict]) -> None:
    """
    Dispara el envío de notificaciones en un hilo daemon (no bloquea la respuesta HTTP).
    alertas_creadas: lista de dicts con keys 'tipo' y 'nivel'.
    """
    if not alertas_creadas:
        return

    def _worker():
        try:
            cfg = _leer_config()
            if cfg.get("notif_email_activa") == "true":
                _enviar_email(cfg, alertas_creadas)
            if cfg.get("notif_whatsapp_activa") == "true":
                _enviar_whatsapp(cfg, alertas_creadas)
        except Exception as exc:
            logger.error(f"Error en worker de notificaciones: {exc}")

    threading.Thread(target=_worker, daemon=True).start()


def probar_whatsapp(
    telefono: str,
    sid: str,
    token: str,
    numero_twilio: str,
) -> dict:
    """Envía un mensaje de WhatsApp de prueba vía Twilio. Retorna dict con ok/mensaje."""
    if not telefono.startswith("+"):
        telefono = "+" + telefono
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        msg = client.messages.create(
            body="✅ SIGPDA — Prueba de conexión WhatsApp correcta. Las alertas llegarán a este número.",
            from_=f"whatsapp:{numero_twilio}",
            to=f"whatsapp:{telefono}",
        )
        return {"ok": True, "mensaje": f"Mensaje enviado a {telefono} (SID: {msg.sid})"}
    except ImportError:
        return {"ok": False, "mensaje": "Twilio no instalado. Ejecuta: pip install twilio"}
    except Exception as exc:
        return {"ok": False, "mensaje": str(exc)}


def probar_email(
    destino: str,
    remitente: str,
    password: str,
) -> dict:
    """Prueba la conexión SMTP y envía un correo de prueba. Retorna dict con ok/error."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "SIGPDA — Prueba de conexión de correo ✓"
    msg["From"] = f"SIGPDA <{remitente}>"
    msg["To"] = destino
    msg.attach(MIMEText(
        "<h3>✅ Configuración correcta</h3>"
        "<p>El correo de notificaciones de SIGPDA está funcionando correctamente.</p>",
        "html", "utf-8",
    ))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(remitente, password)
            smtp.sendmail(remitente, destino, msg.as_string())
        return {"ok": True, "mensaje": f"Correo de prueba enviado a {destino}"}
    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "mensaje": "Credenciales incorrectas. Usa una contraseña de aplicación Gmail."}
    except Exception as exc:
        return {"ok": False, "mensaje": str(exc)}
