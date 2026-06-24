import { NextRequest, NextResponse } from "next/server";
import sql from "@/lib/db";

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const [viaje] = await sql`
      SELECT viajes.*, users.nombre, users.apellido, users.telefono,
             users.id AS conductor_id, users.avatar_data,
             COALESCE(ROUND(AVG(r.estrellas)::numeric, 1), 0) AS promedio_conductor,
             COUNT(r.id) AS total_resenas
      FROM viajes
      JOIN users ON viajes.user_id = users.id
      LEFT JOIN resenas r ON r.receptor_id = users.id
      WHERE viajes.id = ${parseInt(id)}
      GROUP BY viajes.id, users.nombre, users.apellido, users.telefono, users.id, users.avatar_data
    `;
    if (!viaje) return NextResponse.json({ error: "Viaje no encontrado." }, { status: 404 });
    return NextResponse.json(viaje);
  } catch {
    return NextResponse.json({ error: "Error al obtener el viaje." }, { status: 500 });
  }
}
