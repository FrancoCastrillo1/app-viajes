import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();

    if (!email || !password) {
      return NextResponse.json({ error: "Email y contraseña son requeridos." }, { status: 400 });
    }

    const [user] = await sql`
      SELECT id, email, nombre, password FROM users WHERE email = ${email.toLowerCase().trim()}
    `;

    if (!user || !await bcrypt.compare(password, user.password)) {
      return NextResponse.json({ error: "Email o contraseña incorrectos." }, { status: 401 });
    }

    const session = await getSession();
    session.userId = user.id;
    session.userEmail = user.email;
    session.userNombre = user.nombre;
    await session.save();

    return NextResponse.json({ message: "¡Bienvenido de nuevo!" });
  } catch {
    return NextResponse.json({ error: "Error interno del servidor." }, { status: 500 });
  }
}
