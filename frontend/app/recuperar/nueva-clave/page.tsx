"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function NuevaClavePage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = e.currentTarget;
    const password = (form.elements.namedItem("password") as HTMLInputElement).value;
    const confirmar = (form.elements.namedItem("confirmar") as HTMLInputElement).value;

    if (password !== confirmar) {
      toast.error("Las contraseñas no coinciden.");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/auth/recuperar/nueva-clave", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password, confirmar }),
      });
      const json = await res.json();
      if (res.ok) {
        toast.success(json.message);
        router.push(json.redirectTo || "/login");
      } else {
        toast.error(json.error);
        if (json.redirectTo) router.push(json.redirectTo);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-logo">
          <Link href="/" className="auth-logo-text">Ruta Compartida</Link>
        </div>
        <h1 className="auth-title">Nueva contraseña</h1>
        <p className="auth-subtitle">Elegí una contraseña segura de al menos 6 caracteres.</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label className="auth-label" htmlFor="password">Nueva contraseña</label>
            <input id="password" name="password" type="password" className="auth-input" required minLength={6} placeholder="Mínimo 6 caracteres" />
          </div>
          <div className="auth-field">
            <label className="auth-label" htmlFor="confirmar">Confirmá la contraseña</label>
            <input id="confirmar" name="confirmar" type="password" className="auth-input" required minLength={6} placeholder="••••••••" />
          </div>
          <button type="submit" className="btn-auth" disabled={loading}>
            {loading ? "Actualizando..." : "Actualizar contraseña"}
          </button>
        </form>
      </div>
    </div>
  );
}
