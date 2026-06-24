import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";

export async function GET() {
  try {
    const viajes = await sql`
      SELECT viajes.*, users.nombre, users.apellido, users.telefono, users.avatar_data,
             users.id AS conductor_id,
             COALESCE(ROUND(AVG(r.estrellas)::numeric, 1), 0) AS promedio_conductor,
             COUNT(r.id) AS total_resenas
      FROM viajes
      JOIN users ON viajes.user_id = users.id
      LEFT JOIN resenas r ON r.receptor_id = users.id
      WHERE viajes.lugares > 0
        AND viajes.estado = 'pendiente'
        AND (viajes.fecha + viajes.hora)::timestamp > NOW()
      GROUP BY viajes.id, users.nombre, users.apellido, users.telefono, users.avatar_data, users.id
      ORDER BY viajes.fecha, viajes.hora
    `;
    return NextResponse.json(viajes);
  } catch {
    return NextResponse.json({ error: "Error al obtener viajes." }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const session = await getSession();
    if (!session.userId) {
      return NextResponse.json({ error: "No autorizado." }, { status: 401 });
    }

    const [userStatus] = await sql`SELECT verificado FROM users WHERE id = ${session.userId}`;
    if (!userStatus?.verificado) {
      return NextResponse.json({ error: "Debés verificar tu cuenta antes de publicar un viaje.", redirectTo: "/verificar" }, { status: 403 });
    }

    const { origen, destino, encuentro, fecha, hora, lugares, precio } = await request.json();

    if (origen === destino) {
      return NextResponse.json({ error: "El origen y el destino no pueden ser iguales." }, { status: 400 });
    }

    const precioNum = parseFloat(precio);
    const lugaresNum = parseInt(lugares);

    if (isNaN(precioNum) || precioNum < 0 || isNaN(lugaresNum) || lugaresNum < 1 || lugaresNum > 8) {
      return NextResponse.json({ error: "Datos del viaje inválidos." }, { status: 400 });
    }

    await sql`
      INSERT INTO viajes (user_id, origen, destino, encuentro, fecha, hora, lugares, precio, estado)
      VALUES (${session.userId}, ${origen}, ${destino}, ${encuentro ?? ""}, ${fecha}, ${hora}, ${lugaresNum}, ${precioNum}, 'pendiente')
    `;

    return NextResponse.json({ message: "Viaje publicado.", redirectTo: "/perfil" });
  } catch {
    return NextResponse.json({ error: "Error al crear el viaje." }, { status: 500 });
  }
}
