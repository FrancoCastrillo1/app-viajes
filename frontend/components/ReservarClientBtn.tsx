"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function ReservarClientBtn({ viajeId }: { viajeId: number }) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleReservar() {
    setLoading(true);
    try {
      const res = await fetch("/api/reservas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ viajeId }),
      });
      const json = await res.json();
      if (res.ok) {
        toast.success(json.message || "¡Viaje reservado exitosamente!");
        router.push("/perfil");
        router.refresh();
      } else {
        toast.error(json.error || "No se pudo reservar.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <button className="btn-reservar" onClick={handleReservar} disabled={loading}>
      {loading ? "Reservando..." : "Reservar lugar"}
    </button>
  );
}
