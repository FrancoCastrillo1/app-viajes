import { NextRequest, NextResponse } from "next/server";
import { unsealData } from "iron-session";
import type { SessionData } from "./lib/auth";
import { sessionOptions } from "./lib/auth";

const PROTECTED_ROUTES = ["/perfil", "/editar-perfil", "/crear-viaje"];

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED_ROUTES.some((r) => pathname.startsWith(r));

  if (!isProtected) return NextResponse.next();

  const cookieValue = request.cookies.get(sessionOptions.cookieName as string)?.value;

  if (!cookieValue) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  try {
    const data = await unsealData<SessionData>(cookieValue, {
      password: sessionOptions.password as string,
    });
    if (!data.userId) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  } catch {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/perfil/:path*", "/editar-perfil/:path*", "/crear-viaje/:path*"],
};
