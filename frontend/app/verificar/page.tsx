"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function VerificarPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const codigo = (e.currentTarget.elements.namedItem("codigo") as HTMLInputElement).value;
    try {
      const res = await fetch("/api/auth/verificar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codigo }),
      });
      const json = await res.json();
      if (res.ok) {
        toast.success(json.message);
        router.push(json.redirectTo || "/viajes");
        router.refresh();
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
        <h2 className="verify-title">Verificá tu cuenta</h2>
        <p className="verify-desc">
          Te enviamos un código de 6 dígitos a tu email.<br />
          Ingresalo acá para activar tu cuenta.
        </p>

        <form onSubmit={handleSubmit}>
          <input
            name="codigo"
            type="text"
            className="verify-code-input"
            maxLength={6}
            placeholder="123456"
            required
            autoFocus
            inputMode="numeric"
          />
          <button type="submit" className="btn-auth" disabled={loading}>
            {loading ? "Verificando..." : "Verificar cuenta"}
          </button>
        </form>

        <p className="verify-hint">
          ¿No recibiste el código? Revisá tu carpeta de spam.<br />
          <Link href="/register" style={{ color: "var(--primary)", fontWeight: 600 }}>
            Volver a registrarse
          </Link>
        </p>
      </div>
    </div>
  );
}
