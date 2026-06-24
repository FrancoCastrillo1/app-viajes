"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function RecuperarPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const email = (e.currentTarget.elements.namedItem("email") as HTMLInputElement).value;
    try {
      const res = await fetch("/api/auth/recuperar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const json = await res.json();
      if (res.ok) {
        toast.success(json.message);
        router.push(json.redirectTo || "/recuperar/verificar");
      } else {
        toast.error(json.error);
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
        <h1 className="auth-title">Recuperar contraseña</h1>
        <p className="auth-subtitle">Ingresá tu email y te enviamos un código de recuperación.</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label className="auth-label" htmlFor="email">Email</label>
            <input id="email" name="email" type="email" className="auth-input" required placeholder="tu@email.com" />
          </div>
          <button type="submit" className="btn-auth" disabled={loading}>
            {loading ? "Enviando..." : "Enviar código"}
          </button>
        </form>

        <div className="auth-footer">
          <Link href="/login">← Volver al inicio de sesión</Link>
        </div>
      </div>
    </div>
  );
}
