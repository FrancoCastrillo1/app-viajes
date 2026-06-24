import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";
import { enviarMailRecuperacion } from "@/lib/email";

function randomCode() {
  return String(Math.floor(Math.random() * 900000) + 100000);
}

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();

    const codigo = randomCode();
    const expiracion = new Date(Date.now() + 15 * 60 * 1000);

    try {
      const [user] = await sql`SELECT id FROM users WHERE email = ${email.toLowerCase().trim()}`;
      if (user) {
        await sql`
          UPDATE users SET reset_codigo = ${codigo}, reset_expiracion = ${expiracion}
          WHERE email = ${email.toLowerCase().trim()}
        `;
        enviarMailRecuperacion(email.toLowerCase().trim(), codigo).catch(() => {});
      }
    } catch {
      // Silencioso — no revelar si el email existe
    }

    const session = await getSession();
    session.resetEmail = email.toLowerCase().trim();
    await session.save();

    return NextResponse.json({
      message: "Si el email está registrado, recibirás un código en tu correo.",
      redirectTo: "/recuperar/verificar",
    });
  } catch {
    return NextResponse.json({ error: "Error interno del servidor." }, { status: 500 });
  }
}
