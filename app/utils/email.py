"""
Funciones de envío de email vía API de Resend.
Diseñadas para correr dentro de threading.Thread (sin Flask app context).
Leen RESEND_API_KEY directamente de os.environ.
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)


def enviar_mail_verificacion(email_destino: str, codigo: str) -> bool:
    api_key = os.environ.get("RESEND_API_KEY")
    url     = "https://api.resend.com/emails"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "from":    "Ruta Compartida <verificacion@rutacompartida.com.ar>",
        "to":      email_destino,
        "subject": "Tu código de verificación - Ruta Compartida",
        "html": f"""
        <div style="font-family:sans-serif;text-align:center;border:2px solid #E76F51;
                    padding:20px;border-radius:15px;max-width:400px;margin:auto;">
            <h2 style="color:#E76F51;">¡Hola! 👋</h2>
            <p>Tu código de seguridad para <strong>Ruta Compartida</strong>:</p>
            <div style="background:#FFEDD5;color:#E76F51;padding:15px;font-size:2rem;
                        font-weight:bold;border-radius:10px;margin:20px 0;letter-spacing:5px;">
                {codigo}
            </div>
            <p style="color:#666;font-size:0.9rem;">
                Si no solicitaste este código, ignorá este mensaje.
            </p>
            <p style="font-size:0.8rem;color:#999;">© 2026 Ruta Compartida</p>
        </div>""",
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        return response.status_code in [200, 201]
    except Exception as e:
        logger.error("Error enviando mail de verificación a %s: %s", email_destino, e, exc_info=True)
        return False


def enviar_mail_recuperacion(email_destino: str, codigo: str) -> bool:
    api_key = os.environ.get("RESEND_API_KEY")
    url     = "https://api.resend.com/emails"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "from":    "Ruta Compartida <verificacion@rutacompartida.com.ar>",
        "to":      email_destino,
        "subject": "Recuperá tu contraseña - Ruta Compartida",
        "html": f"""
        <div style="font-family:sans-serif;text-align:center;border:2px solid #E76F51;
                    padding:20px;border-radius:15px;max-width:400px;margin:auto;">
            <h2 style="color:#E76F51;">Recuperar contraseña</h2>
            <p>Usá este código para restablecer tu contraseña en <strong>Ruta Compartida</strong>:</p>
            <div style="background:#FFEDD5;color:#E76F51;padding:15px;font-size:2rem;
                        font-weight:bold;border-radius:10px;margin:20px 0;letter-spacing:5px;">
                {codigo}
            </div>
            <p style="color:#666;font-size:0.9rem;">
                El código expira en 15 minutos.<br>
                Si no solicitaste esto, ignorá este mensaje.
            </p>
            <p style="font-size:0.8rem;color:#999;">© 2026 Ruta Compartida</p>
        </div>""",
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        return response.status_code in [200, 201]
    except Exception as e:
        logger.error("Error enviando mail de recuperación a %s: %s", email_destino, e, exc_info=True)
        return False


def enviar_aviso(email_destino: str, asunto: str, mensaje: str) -> None:
    api_key = os.environ.get("RESEND_API_KEY")
    url     = "https://api.resend.com/emails"
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
        <div style="background:#E76F51;color:white;padding:15px;">
            <h1>Ruta Compartida</h1>
        </div>
        <div style="padding:20px;">{mensaje}</div>
        <div style="background:#f2f2f2;padding:10px;text-align:center;">
            <small>© 2026 Ruta Compartida</small>
        </div>
    </div>"""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data    = {
        "from":    "Ruta Compartida <avisos@rutacompartida.com.ar>",
        "to":      email_destino,
        "subject": asunto,
        "html":    html_body,
    }
    try:
        requests.post(url, headers=headers, json=data, timeout=10)
    except Exception as e:
        logger.error("Error enviando aviso a %s: %s", email_destino, e, exc_info=True)
