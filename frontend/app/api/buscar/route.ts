import { NextRequest, NextResponse } from "next/server";
import sql from "@/lib/db";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const origen  = searchParams.get("origen")  || "";
    const destino = searchParams.get("destino") || "";
    const fecha   = searchParams.get("fecha")   || "";

    const viajes = await sql`
      SELECT viajes.*, users.nombre, users.apellido, users.telefono, users.avatar_data,
             users.id AS conductor_id,
             COALESCE(ROUND(AVG(r.estrellas)::numeric, 1), 0) AS promedio_conductor,
             COUNT(r.id) AS total_resenas
      FROM viajes
      JOIN users ON viajes.user_id = users.id
      LEFT JOIN resenas r ON r.receptor_id = users.id
      WHERE viajes.estado = 'pendiente'
        AND viajes.lugares > 0
        AND (viajes.fecha + viajes.hora)::timestamp > NOW()
        ${origen  ? sql`AND viajes.origen  ILIKE ${"%" + origen  + "%"}` : sql``}
        ${destino ? sql`AND viajes.destino ILIKE ${"%" + destino + "%"}` : sql``}
        ${fecha   ? sql`AND viajes.fecha = ${fecha}`                      : sql``}
      GROUP BY viajes.id, users.nombre, users.apellido, users.telefono, users.avatar_data, users.id
      ORDER BY viajes.fecha ASC
    `;

    return NextResponse.json(viajes);
  } catch {
    return NextResponse.json({ error: "Error en la búsqueda." }, { status: 500 });
  }
}
