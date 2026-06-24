import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";

export async function POST(request: NextRequest) {
  try {
    const session = await getSession();

    if (!session.userId) {
      return NextResponse.json({ error: "No autorizado." }, { status: 401 });
    }

    const { codigo } = await request.json();

    const [user] = await sql`
      SELECT codigo_verificacion, codigo_expiracion
      FROM users WHERE id = ${session.userId}
    `;

    if (!user) {
      return NextResponse.json({ error: "Usuario no encontrado." }, { status: 404 });
    }

    if (user.codigo_expiracion && new Date(user.codigo_expiracion) < new Date()) {
      session.destroy();
      return NextResponse.json({ error: "El código expiró. Registrate nuevamente.", redirectTo: "/register" }, { status: 400 });
    }

    if (user.codigo_verificacion !== String(codigo)) {
      return NextResponse.json({ error: "Código incorrecto. Intentá de nuevo." }, { status: 400 });
    }

    await sql`UPDATE users SET verificado = TRUE WHERE id = ${session.userId}`;

    return NextResponse.json({ message: "¡Cuenta verificada con éxito!", redirectTo: "/viajes" });
  } catch {
    return NextResponse.json({ error: "Error interno del servidor." }, { status: 500 });
  }
}
