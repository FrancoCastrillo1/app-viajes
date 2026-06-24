"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Link from "next/link";

export default function EditarPerfilPage() {
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  // Carga inicial de datos del perfil
  if (!initialized) {
    setInitialized(true);
    fetch("/api/perfil")
      .then((r) => r.json())
      .then((data) => {
        if (data.user) {
          setNombre(data.user.nombre || "");
          setApellido(data.user.apellido || "");
          if (data.user.avatar_data) setAvatarPreview(data.user.avatar_data);
        }
      });
  }

  function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => setAvatarPreview(ev.target?.result as string);
      reader.readAsDataURL(file);
    }
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = e.currentTarget;
    const formData = new FormData();
    formData.set("nombre", nombre);
    formData.set("apellido", apellido);

    const pwd = (form.elements.namedItem("nueva_password") as HTMLInputElement).value;
    if (pwd) formData.set("nueva_password", pwd);

    const avatarFile = fileRef.current?.files?.[0];
    if (avatarFile) formData.set("avatar", avatarFile);

    try {
      const res = await fetch("/api/perfil", { method: "PATCH", body: formData });
      const json = await res.json();
      if (res.ok) {
        toast.success(json.message);
        router.push("/perfil");
        router.refresh();
      } else {
        toast.error(json.error);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="crear-wrapper">
      <div className="crear-header">
        <h1>Editar perfil</h1>
        <p>Actualizá tu información personal.</p>
      </div>

      <div className="crear-card">
        <form onSubmit={handleSubmit} className="crear-form">
          <div className="section-sep"><span>Foto de perfil</span></div>

          <div className="avatar-upload-wrap">
            {avatarPreview ? (
              <img src={avatarPreview} alt="Avatar" className="avatar-preview" />
            ) : (
              <div className="avatar-preview-placeholder">👤</div>
            )}
            <div>
              <label className="btn-avatar-upload" htmlFor="avatar-file">
                📷 Cambiar foto
              </label>
              <input
                id="avatar-file"
                type="file"
                accept="image/*"
                style={{ display: "none" }}
                ref={fileRef}
                onChange={handleAvatarChange}
              />
              <p className="avatar-hint">JPG, PNG o WebP. Máximo 2MB.</p>
            </div>
          </div>

          <div className="section-sep"><span>Datos personales</span></div>

          <div className="crear-row">
            <div className="crear-field">
              <label className="crear-label" htmlFor="nombre">Nombre</label>
              <input id="nombre" type="text" className="crear-input" value={nombre} onChange={(e) => setNombre(e.target.value)} required />
            </div>
            <div className="crear-field">
              <label className="crear-label" htmlFor="apellido">Apellido</label>
              <input id="apellido" type="text" className="crear-input" value={apellido} onChange={(e) => setApellido(e.target.value)} required />
            </div>
          </div>

          <div className="section-sep"><span>Cambiar contraseña (opcional)</span></div>

          <div className="crear-field">
            <label className="crear-label" htmlFor="nueva_password">Nueva contraseña</label>
            <input id="nueva_password" name="nueva_password" type="password" className="crear-input" placeholder="Dejá vacío para no cambiarla" minLength={6} />
          </div>

          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <button type="submit" className="btn-publicar" disabled={loading} style={{ flex: 1 }}>
              {loading ? "Guardando..." : "Guardar cambios"}
            </button>
            <Link href="/perfil" className="btn-danger" style={{ textDecoration: "none", display: "flex", alignItems: "center", justifyContent: "center", padding: "17px 20px" }}>
              Cancelar
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
