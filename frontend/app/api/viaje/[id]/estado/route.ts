import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";

const ESTADOS_VALIDOS = ["pendiente", "en_viaje", "finalizado"];

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const session = await getSession();
    if (!session.userId) {
      return NextResponse.json({ error: "No autorizado." }, { status: 401 });
    }

    const { id } = await params;
    const { estado } = await request.json();

    if (!ESTADOS_VALIDOS.includes(estado)) {
      return NextResponse.json({ error: "Estado no válido." }, { status: 400 });
    }

    const [viaje] = await sql`SELECT user_id FROM viajes WHERE id = ${parseInt(id)}`;
    if (!viaje || viaje.user_id !== session.userId) {
      return NextResponse.json({ error: "No tenés permiso para modificar este viaje." }, { status: 403 });
    }

    await sql`UPDATE viajes SET estado = ${estado} WHERE id = ${parseInt(id)}`;

    return NextResponse.json({ message: "Estado del viaje actualizado." });
  } catch {
    return NextResponse.json({ error: "Error al cambiar el estado." }, { status: 500 });
  }
}
