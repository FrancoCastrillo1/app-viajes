import { Resend } from "resend";

function getResend() {
  return new Resend(process.env.RESEND_API_KEY);
}

export async function enviarMailVerificacion(emailDestino: string, codigo: string) {
  await getResend().emails.send({
    from: "Ruta Compartida <verificacion@rutacompartida.com.ar>",
    to: emailDestino,
    subject: "Tu código de verificación - Ruta Compartida",
    html: `
    <div style="font-family:sans-serif;text-align:center;border:2px solid #E76F51;
                padding:20px;border-radius:15px;max-width:400px;margin:auto;">
        <h2 style="color:#E76F51;">¡Hola! 👋</h2>
        <p>Tu código de seguridad para <strong>Ruta Compartida</strong>:</p>
        <div style="background:#FFEDD5;color:#E76F51;padding:15px;font-size:2rem;
                    font-weight:bold;border-radius:10px;margin:20px 0;letter-spacing:5px;">
            ${codigo}
        </div>
        <p style="color:#666;font-size:0.9rem;">
            Si no solicitaste este código, ignorá este mensaje.
        </p>
        <p style="font-size:0.8rem;color:#999;">© 2026 Ruta Compartida</p>
    </div>`,
  });
}

export async function enviarMailRecuperacion(emailDestino: string, codigo: string) {
  await getResend().emails.send({
    from: "Ruta Compartida <verificacion@rutacompartida.com.ar>",
    to: emailDestino,
    subject: "Recuperá tu contraseña - Ruta Compartida",
    html: `
    <div style="font-family:sans-serif;text-align:center;border:2px solid #E76F51;
                padding:20px;border-radius:15px;max-width:400px;margin:auto;">
        <h2 style="color:#E76F51;">Recuperar contraseña</h2>
        <p>Usá este código para restablecer tu contraseña en <strong>Ruta Compartida</strong>:</p>
        <div style="background:#FFEDD5;color:#E76F51;padding:15px;font-size:2rem;
                    font-weight:bold;border-radius:10px;margin:20px 0;letter-spacing:5px;">
            ${codigo}
        </div>
        <p style="color:#666;font-size:0.9rem;">
            El código expira en 15 minutos.<br>
            Si no solicitaste esto, ignorá este mensaje.
        </p>
        <p style="font-size:0.8rem;color:#999;">© 2026 Ruta Compartida</p>
    </div>`,
  });
}

export async function enviarAviso(emailDestino: string, asunto: string, mensaje: string) {
  await getResend().emails.send({
    from: "Ruta Compartida <avisos@rutacompartida.com.ar>",
    to: emailDestino,
    subject: asunto,
    html: `
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
        <div style="background:#E76F51;color:white;padding:15px;">
            <h1>Ruta Compartida</h1>
        </div>
        <div style="padding:20px;">${mensaje}</div>
        <div style="background:#f2f2f2;padding:10px;text-align:center;">
            <small>© 2026 Ruta Compartida</small>
        </div>
    </div>`,
  });
}
