import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";
import { enviarAviso } from "@/lib/email";

export async function POST(request: NextRequest) {
  try {
    const session = await getSession();
    if (!session.userId) {
      return NextResponse.json({ error: "No autorizado." }, { status: 401 });
    }
    const userId = session.userId;

    const { viajeId } = await request.json();

    const [yaReservo] = await sql`
      SELECT id FROM reservas WHERE viaje_id = ${viajeId} AND user_id = ${userId}
    `;
    if (yaReservo) {
      return NextResponse.json({ error: "Ya tenés una reserva en este viaje." }, { status: 409 });
    }

    const [viaje] = await sql`
      SELECT v.*, u.email AS conductor_email, u.nombre AS conductor_nombre
      FROM viajes v
      JOIN users u ON v.user_id = u.id
      WHERE v.id = ${viajeId}
    `;

    if (!viaje) {
      return NextResponse.json({ error: "Viaje no encontrado." }, { status: 404 });
    }

    if (viaje.user_id === userId) {
      return NextResponse.json({ error: "No podés reservar tu propio viaje." }, { status: 400 });
    }

    if (viaje.lugares <= 0 || viaje.estado !== "pendiente") {
      return NextResponse.json({ error: "No se pudo reservar el viaje." }, { status: 400 });
    }

    // Transacción atómica
    await sql.begin(async (tx) => {
      await tx`INSERT INTO reservas (viaje_id, user_id) VALUES (${viajeId}, ${userId})`;
      await tx`UPDATE viajes SET lugares = lugares - 1 WHERE id = ${viajeId} AND lugares > 0`;
    });

    // Emails en background
    enviarAviso(
      session.userEmail!,
      "Reserva Confirmada",
      `<h2>✅ Reserva confirmada</h2><p>Tu viaje ${viaje.origen} → ${viaje.destino} del ${viaje.fecha} está reservado.</p>`,
    ).catch(() => {});
    enviarAviso(
      viaje.conductor_email,
      "Nuevo Pasajero",
      `<h2>🚗 Nuevo pasajero</h2><p>${session.userNombre} reservó un lugar en tu viaje ${viaje.origen} → ${viaje.destino}.</p>`,
    ).catch(() => {});

    return NextResponse.json({ message: "¡Viaje reservado exitosamente!" });
  } catch {
    return NextResponse.json({ error: "No se pudo reservar." }, { status: 500 });
  }
}
