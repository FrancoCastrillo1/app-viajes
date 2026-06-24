import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";
import { processAvatar } from "@/lib/images";

export async function GET() {
  try {
    const session = await getSession();
    if (!session.userId) return NextResponse.json({ error: "No autorizado." }, { status: 401 });

    const [user] = await sql`
      SELECT nombre, apellido, telefono, email, avatar_data FROM users WHERE id = ${session.userId}
    `;

    const misReservas = await sql`
      SELECT viajes.*, reservas.id AS reserva_id,
             conductor.nombre AS conductor_nombre, conductor.apellido AS conductor_apellido,
             conductor.telefono AS conductor_telefono, conductor.id AS conductor_id
      FROM reservas
      JOIN viajes ON reservas.viaje_id = viajes.id
      JOIN users AS conductor ON viajes.user_id = conductor.id
      WHERE reservas.user_id = ${session.userId}
      ORDER BY viajes.fecha DESC
    `;

    const misPublicaciones = await sql`
      SELECT * FROM viajes WHERE user_id = ${session.userId} ORDER BY fecha DESC
    `;

    const pasajeros = await sql`
      SELECT reservas.viaje_id, reservas.id AS reserva_id,
             users.nombre, users.apellido, users.telefono, users.id AS pasajero_id
      FROM reservas
      JOIN users ON reservas.user_id = users.id
      WHERE reservas.viaje_id IN (SELECT id FROM viajes WHERE user_id = ${session.userId})
    `;

    const resenasRecibidas = await sql`
      SELECT r.estrellas, r.comentario, r.created_at,
             u.nombre AS autor_nombre, u.apellido AS autor_apellido
      FROM resenas r
      JOIN users u ON r.autor_id = u.id
      WHERE r.receptor_id = ${session.userId}
      ORDER BY r.created_at DESC
    `;

    const resenasEnviadas = await sql`
      SELECT viaje_id, receptor_id FROM resenas WHERE autor_id = ${session.userId}
    `;

    return NextResponse.json({
      user,
      misReservas,
      viajes: misPublicaciones,
      pasajeros,
      resenas: resenasRecibidas,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      resenasEnviadas: (resenasEnviadas as any[]).map((r) => `${r.viaje_id}-${r.receptor_id}`),
    });
  } catch {
    return NextResponse.json({ error: "Error al obtener el perfil." }, { status: 500 });
  }
}

export async function PATCH(request: NextRequest) {
  try {
    const session = await getSession();
    if (!session.userId) return NextResponse.json({ error: "No autorizado." }, { status: 401 });

    const formData = await request.formData();
    const nombre        = String(formData.get("nombre") || "").trim();
    const apellido      = String(formData.get("apellido") || "").trim();
    const nuevaPassword = String(formData.get("nueva_password") || "").trim();
    const avatarFile    = formData.get("avatar") as File | null;

    let avatarData: string | null = null;

    if (avatarFile && avatarFile.size > 0) {
      const buffer = Buffer.from(await avatarFile.arrayBuffer());
      const ext = avatarFile.name.split(".").pop() || "";
      const result = await processAvatar(buffer, ext);
      if ("error" in result) {
        return NextResponse.json({ error: result.error }, { status: 400 });
      }
      avatarData = result.dataUrl;
    }

    if (nuevaPassword) {
      if (nuevaPassword.length < 6) {
        return NextResponse.json({ error: "La contraseña debe tener al menos 6 caracteres." }, { status: 400 });
      }
      const hashed = await bcrypt.hash(nuevaPassword, 10);
      if (avatarData) {
        await sql`UPDATE users SET nombre=${nombre}, apellido=${apellido}, password=${hashed}, avatar_data=${avatarData} WHERE id=${session.userId}`;
      } else {
        await sql`UPDATE users SET nombre=${nombre}, apellido=${apellido}, password=${hashed} WHERE id=${session.userId}`;
      }
    } else {
      if (avatarData) {
        await sql`UPDATE users SET nombre=${nombre}, apellido=${apellido}, avatar_data=${avatarData} WHERE id=${session.userId}`;
      } else {
        await sql`UPDATE users SET nombre=${nombre}, apellido=${apellido} WHERE id=${session.userId}`;
      }
    }

    session.userNombre = nombre;
    await session.save();

    return NextResponse.json({ message: "¡Perfil actualizado con éxito!" });
  } catch {
    return NextResponse.json({ error: "Error al actualizar el perfil." }, { status: 500 });
  }
}
