import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";
import { enviarMailVerificacion } from "@/lib/email";

function randomCode() {
  return String(Math.floor(Math.random() * 900000) + 100000);
}

export async function POST(request: NextRequest) {
  try {
    const { nombre, apellido, telefono, email, password } = await request.json();

    if (!nombre || !apellido || !email || !password) {
      return NextResponse.json({ error: "Todos los campos son requeridos." }, { status: 400 });
    }

    const codigo = randomCode();
    const expiracion = new Date(Date.now() + 15 * 60 * 1000);
    const hash = await bcrypt.hash(password, 10);

    let newUser;
    try {
      [newUser] = await sql`
        INSERT INTO users (nombre, apellido, telefono, email, password, codigo_verificacion, codigo_expiracion, verificado)
        VALUES (${nombre.trim()}, ${apellido.trim()}, ${telefono?.trim() ?? ""}, ${email.toLowerCase().trim()},
                ${hash}, ${codigo}, ${expiracion}, FALSE)
        RETURNING id
      `;
    } catch (err: unknown) {
      const pgErr = err as { code?: string };
      if (pgErr.code === "23505") {
        return NextResponse.json({ error: "Este email ya está registrado. Por favor, iniciá sesión." }, { status: 409 });
      }
      throw err;
    }

    enviarMailVerificacion(email.toLowerCase().trim(), codigo).catch(() => {});

    const session = await getSession();
    session.userId = newUser.id;
    session.userEmail = email.toLowerCase().trim();
    session.userNombre = nombre.trim();
    await session.save();

    return NextResponse.json({ message: "Registro exitoso.", redirectTo: "/verificar" });
  } catch {
    return NextResponse.json({ error: "Error interno del servidor." }, { status: 500 });
  }
}
