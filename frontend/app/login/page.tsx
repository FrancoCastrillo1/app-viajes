"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = e.currentTarget;
    const data = {
      email: (form.elements.namedItem("email") as HTMLInputElement).value,
      password: (form.elements.namedItem("password") as HTMLInputElement).value,
    };
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const json = await res.json();
      if (res.ok) {
        toast.success(json.message);
        router.push("/viajes");
        router.refresh();
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
          <p>Viajá junto a otros, lleguen más lejos.</p>
        </div>
        <h1 className="auth-title">Iniciá sesión</h1>
        <p className="auth-subtitle">Ingresá a tu cuenta para continuar.</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label className="auth-label" htmlFor="email">Email</label>
            <input id="email" name="email" type="email" className="auth-input" required placeholder="tu@email.com" />
          </div>
          <div className="auth-field">
            <label className="auth-label" htmlFor="password">Contraseña</label>
            <input id="password" name="password" type="password" className="auth-input" required placeholder="••••••••" />
          </div>
          <div className="auth-forgot">
            <Link href="/recuperar">¿Olvidaste tu contraseña?</Link>
          </div>
          <button type="submit" className="btn-auth" disabled={loading}>
            {loading ? "Ingresando..." : "Ingresar"}
          </button>
        </form>

        <div className="auth-footer">
          ¿No tenés cuenta? <Link href="/register">Registrate</Link>
        </div>
      </div>
    </div>
  );
}
