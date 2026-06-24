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
    const reservaId = parseInt(id);

    const [datos] = await sql`
      SELECT r.viaje_id, r.user_id, u.email AS conductor_email
      FROM reservas r
      JOIN viajes v ON r.viaje_id = v.id
      JOIN users u ON v.user_id = u.id
      WHERE r.id = ${reservaId}
    `;

    if (!datos || datos.user_id !== session.userId) {
      return NextResponse.json({ error: "No podés cancelar esta reserva." }, { status: 403 });
    }

    await sql.begin(async (tx) => {
      await tx`DELETE FROM reservas WHERE id = ${reservaId}`;
      await tx`UPDATE viajes SET lugares = lugares + 1 WHERE id = ${datos.viaje_id}`;
    });

    enviarAviso(
      datos.conductor_email,
      "Lugar liberado",
      "Un pasajero canceló su lugar en tu viaje.",
    ).catch(() => {});

    return NextResponse.json({ message: "Reserva cancelada." });
  } catch {
    return NextResponse.json({ error: "No se pudo cancelar la reserva." }, { status: 500 });
  }
}
