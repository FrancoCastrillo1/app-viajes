import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";
import { enviarAviso } from "@/lib/email";

export async function DELETE(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const session = await getSession();
    if (!session.userId) {
      return NextResponse.json({ error: "No autorizado." }, { status: 401 });
    }

    const { id } = await params;
    const viajeId = parseInt(id);

    const [viaje] = await sql`SELECT user_id FROM viajes WHERE id = ${viajeId}`;
    if (!viaje || viaje.user_id !== session.userId) {
      return NextResponse.json({ error: "No tenés permiso para cancelar este viaje." }, { status: 403 });
    }

    const pasajeros = await sql`
      SELECT u.email FROM reservas r JOIN users u ON r.user_id = u.id WHERE r.viaje_id = ${viajeId}
    `;

    await sql.begin(async (tx) => {
      await tx`DELETE FROM reservas WHERE viaje_id = ${viajeId}`;
      await tx`DELETE FROM viajes WHERE id = ${viajeId}`;
    });

    for (const p of pasajeros) {
      enviarAviso(p.email, "Viaje Cancelado", "El conductor canceló el viaje.").catch(() => {});
    }

    return NextResponse.json({ message: "Viaje cancelado." });
  } catch {
    return NextResponse.json({ error: "Error al cancelar el viaje." }, { status: 500 });
  }
}
