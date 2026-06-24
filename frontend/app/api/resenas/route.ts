import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";

export async function POST(request: NextRequest) {
  try {
    const session = await getSession();
    if (!session.userId) {
      return NextResponse.json({ error: "No autorizado." }, { status: 401 });
    }

    const { viajeId, receptorId, estrellas, comentario } = await request.json();

    const estrellasNum = parseInt(estrellas);
    if (isNaN(estrellasNum) || estrellasNum < 1 || estrellasNum > 5) {
      return NextResponse.json({ error: "Calificación inválida." }, { status: 400 });
    }

    const [viaje] = await sql`
      SELECT id, user_id FROM viajes WHERE id = ${viajeId} AND estado = 'finalizado'
    `;
    if (!viaje) {
      return NextResponse.json({ error: "Solo podés calificar viajes finalizados." }, { status: 400 });
    }

    const esConductor = viaje.user_id === session.userId;
    const [esPasajero] = await sql`
      SELECT id FROM reservas WHERE viaje_id = ${viajeId} AND user_id = ${session.userId}
    `;

    if (!esConductor && !esPasajero) {
      return NextResponse.json({ error: "Solo podés calificar viajes en los que participaste." }, { status: 403 });
    }

    if (receptorId === session.userId) {
      return NextResponse.json({ error: "No podés calificarte a vos mismo." }, { status: 400 });
    }

    await sql`
      INSERT INTO resenas (viaje_id, autor_id, receptor_id, estrellas, comentario)
      VALUES (${viajeId}, ${session.userId}, ${receptorId}, ${estrellasNum}, ${comentario?.slice(0, 500) ?? ""})
      ON CONFLICT (viaje_id, autor_id, receptor_id) DO NOTHING
    `;

    return NextResponse.json({ message: "¡Reseña enviada!" });
  } catch {
    return NextResponse.json({ error: "No se pudo enviar la reseña." }, { status: 500 });
  }
}
