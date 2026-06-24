"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function RegisterPage() {
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
    if (password.length < 6) {
      toast.error("La contraseña debe tener al menos 6 caracteres.");
      setLoading(false);
      return;
    }

    const data = {
      nombre: (form.elements.namedItem("nombre") as HTMLInputElement).value,
      apellido: (form.elements.namedItem("apellido") as HTMLInputElement).value,
      telefono: (form.elements.namedItem("telefono") as HTMLInputElement).value,
      email: (form.elements.namedItem("email") as HTMLInputElement).value,
      password,
    };

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const json = await res.json();
      if (res.ok) {
        router.push(json.redirectTo || "/verificar");
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
      <div className="auth-card auth-card-wide">
        <div className="auth-logo">
          <Link href="/" className="auth-logo-text">Ruta Compartida</Link>
          <p>Creá tu cuenta y empezá a viajar.</p>
        </div>
        <h1 className="auth-title">Crear cuenta</h1>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-row">
            <div className="auth-field">
              <label className="auth-label" htmlFor="nombre">Nombre</label>
              <input id="nombre" name="nombre" type="text" className="auth-input" required placeholder="Juan" />
            </div>
            <div className="auth-field">
              <label className="auth-label" htmlFor="apellido">Apellido</label>
              <input id="apellido" name="apellido" type="text" className="auth-input" required placeholder="Pérez" />
            </div>
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="telefono">Teléfono (WhatsApp)</label>
            <input id="telefono" name="telefono" type="tel" className="auth-input" placeholder="3464123456" />
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="email">Email</label>
            <input id="email" name="email" type="email" className="auth-input" required placeholder="tu@email.com" />
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="password">Contraseña</label>
            <input id="password" name="password" type="password" className="auth-input" required placeholder="Mínimo 6 caracteres" minLength={6} />
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="confirmar">Confirmá tu contraseña</label>
            <input id="confirmar" name="confirmar" type="password" className="auth-input" required placeholder="••••••••" />
          </div>

          <p className="auth-terms">
            Al registrarte aceptás los{" "}
            <Link href="/terminos">Términos y Condiciones</Link>.
          </p>

          <button type="submit" className="btn-auth" disabled={loading}>
            {loading ? "Creando cuenta..." : "Crear cuenta"}
          </button>
        </form>

        <div className="auth-footer">
          ¿Ya tenés cuenta? <Link href="/login">Iniciá sesión</Link>
        </div>
      </div>
    </div>
  );
}
