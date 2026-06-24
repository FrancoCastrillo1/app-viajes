import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";

export async function POST(request: NextRequest) {
  try {
    const session = await getSession();

    if (!session.resetEmail) {
      return NextResponse.json({ error: "Sesión expirada.", redirectTo: "/recuperar" }, { status: 400 });
    }

    const { codigo } = await request.json();
    const email = session.resetEmail;

    const [user] = await sql`
      SELECT reset_codigo, reset_expiracion FROM users WHERE email = ${email}
    `;

    if (!user || !user.reset_codigo) {
      return NextResponse.json({ error: "No hay una solicitud de recuperación activa.", redirectTo: "/recuperar" }, { status: 400 });
    }

    if (user.reset_expiracion && new Date(user.reset_expiracion) < new Date()) {
      return NextResponse.json({ error: "El código expiró. Solicitá uno nuevo.", redirectTo: "/recuperar" }, { status: 400 });
    }

    if (user.reset_codigo !== String(codigo)) {
      return NextResponse.json({ error: "Código incorrecto. Intentá de nuevo." }, { status: 400 });
    }

    session.resetVerificado = true;
    await session.save();

    return NextResponse.json({ redirectTo: "/recuperar/nueva-clave" });
  } catch {
    return NextResponse.json({ error: "Error interno del servidor." }, { status: 500 });
  }
}
