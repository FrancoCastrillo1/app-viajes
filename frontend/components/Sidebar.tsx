"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  userId?: number;
}

export default function Sidebar({ isOpen, onClose, userId }: SidebarProps) {
  const router = useRouter();

  async function handleLogout() {
    const res = await fetch("/api/auth/logout", { method: "POST" });
    if (res.ok) {
      onClose();
      router.push("/");
      router.refresh();
    } else {
      toast.error("Error al cerrar sesión.");
    }
  }

  return (
    <div
      id="mySidebar"
      className="sidebar"
      style={{ width: isOpen ? "260px" : "0" }}
    >
      <button className="closebtn" onClick={onClose} aria-label="Cerrar menú">
        &times;
      </button>
      <Link href="/" onClick={onClose}>🏠 Inicio</Link>
      <Link href="/viajes" onClick={onClose}>🔍 Ver viajes</Link>
      {userId ? (
        <>
          <Link href="/perfil" onClick={onClose}>👤 Mi Perfil</Link>
          <Link href="/crear-viaje" onClick={onClose}>🚗 Publicar viaje</Link>
          <hr className="sidebar-sep" />
          <button className="sidebar-logout-btn" onClick={handleLogout}>
            🚪 Cerrar sesión
          </button>
        </>
      ) : (
        <>
          <Link href="/login" onClick={onClose}>🔑 Ingresar</Link>
          <Link href="/register" onClick={onClose}>📝 Registrarse</Link>
        </>
      )}
    </div>
  );
}
