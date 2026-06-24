"use client";

import Link from "next/link";

interface NavbarProps {
  userId?: number;
  onOpenSidebar: () => void;
}

export default function Navbar({ userId, onOpenSidebar }: NavbarProps) {
  return (
    <nav className="navbar">
      <div className="nav-inner">
        <div className="nav-left">
          {userId ? (
            <button className="hamburger" onClick={onOpenSidebar} aria-label="Abrir menú">
              <span></span>
              <span></span>
              <span></span>
            </button>
          ) : (
            <Link href="/viajes" className="nav-link">Ver viajes</Link>
          )}
        </div>

        <Link href="/" className="nav-logo">Ruta Compartida</Link>

        <div className="nav-right">
          {!userId ? (
            <>
              <Link href="/login" className="nav-link">Ingresar</Link>
              <Link href="/register" className="nav-cta">Registrarse</Link>
            </>
          ) : (
            <Link href="/crear-viaje" className="nav-cta">+ Publicar</Link>
          )}
        </div>
      </div>
    </nav>
  );
}
