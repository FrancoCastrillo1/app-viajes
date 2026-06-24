import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";

export async function POST(request: NextRequest) {
  try {
    const session = await getSession();

    if (!session.resetEmail || !session.resetVerificado) {
      return NextResponse.json({ error: "Sesión expirada.", redirectTo: "/recuperar" }, { status: 400 });
    }

    const { password, confirmar } = await request.json();

    if (password !== confirmar) {
      return NextResponse.json({ error: "Las contraseñas no coinciden." }, { status: 400 });
    }

    if (!password || password.length < 6) {
      return NextResponse.json({ error: "La contraseña debe tener al menos 6 caracteres." }, { status: 400 });
    }

    const hash = await bcrypt.hash(password, 10);
    await sql`
      UPDATE users SET password = ${hash}, reset_codigo = NULL, reset_expiracion = NULL
      WHERE email = ${session.resetEmail}
    `;

    session.resetEmail = undefined;
    session.resetVerificado = undefined;
    await session.save();

    return NextResponse.json({
      message: "¡Contraseña actualizada con éxito! Podés iniciar sesión.",
      redirectTo: "/login",
    });
  } catch {
    return NextResponse.json({ error: "Error interno del servidor." }, { status: 500 });
  }
}
