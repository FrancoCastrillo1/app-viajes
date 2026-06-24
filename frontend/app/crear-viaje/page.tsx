"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { CITIES } from "@/lib/cities";

export default function CrearViajePage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const today = new Date().toISOString().split("T")[0];

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = e.currentTarget;
    const get = (name: string) => (form.elements.namedItem(name) as HTMLInputElement | HTMLSelectElement).value;

    const origen  = get("origen");
    const destino = get("destino");

    if (origen === destino) {
      toast.error("El origen y el destino no pueden ser iguales.");
      setLoading(false);
      return;
    }

    const precio  = parseFloat(get("precio"));
    const lugares = parseInt(get("lugares"));

    if (isNaN(precio) || precio < 0) {
      toast.error("El precio debe ser un número positivo.");
      setLoading(false);
      return;
    }
    if (isNaN(lugares) || lugares < 1 || lugares > 8) {
      toast.error("Los lugares disponibles deben estar entre 1 y 8.");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/viajes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origen, destino,
          encuentro: get("encuentro"),
          fecha: get("fecha"),
          hora: get("hora"),
          lugares, precio,
        }),
      });
      const json = await res.json();
      if (res.ok) {
        toast.success("¡Viaje publicado con éxito!");
        router.push(json.redirectTo || "/perfil");
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
    <div className="crear-wrapper">
      <div className="crear-header">
        <h1>Publicar viaje</h1>
        <p>Completá los datos de tu viaje y encontrá pasajeros en tu ruta.</p>
      </div>

      <div className="crear-card">
        <form onSubmit={handleSubmit} className="crear-form">
          <div className="section-sep"><span>Ruta</span></div>

          <div className="crear-row">
            <div className="crear-field">
              <label className="crear-label" htmlFor="origen">Origen</label>
              <select id="origen" name="origen" className="crear-select" required>
                <option value="">Seleccioná origen</option>
                {CITIES.map((c) => <option key={c.value} value={c.value}>{c.display}</option>)}
              </select>
            </div>
            <div className="crear-field">
              <label className="crear-label" htmlFor="destino">Destino</label>
              <select id="destino" name="destino" className="crear-select" required>
                <option value="">Seleccioná destino</option>
                {CITIES.map((c) => <option key={c.value} value={c.value}>{c.display}</option>)}
              </select>
            </div>
          </div>

          <div className="crear-field">
            <label className="crear-label" htmlFor="encuentro">Punto de encuentro (opcional)</label>
            <input id="encuentro" name="encuentro" type="text" className="crear-input" placeholder="Ej: Terminal de Leones, YPF Ruta 4..." />
          </div>

          <div className="section-sep"><span>Fecha y hora</span></div>

          <div className="crear-row">
            <div className="crear-field">
              <label className="crear-label" htmlFor="fecha">Fecha</label>
              <input id="fecha" name="fecha" type="date" className="crear-input" min={today} required />
            </div>
            <div className="crear-field">
              <label className="crear-label" htmlFor="hora">Hora de salida</label>
              <input id="hora" name="hora" type="time" className="crear-input" required />
            </div>
          </div>

          <div className="section-sep"><span>Detalles</span></div>

          <div className="crear-row">
            <div className="crear-field">
              <label className="crear-label" htmlFor="lugares">Lugares disponibles</label>
              <select id="lugares" name="lugares" className="crear-select" required>
                {[1,2,3,4,5,6,7,8].map((n) => (
                  <option key={n} value={n}>{n} lugar{n !== 1 ? "es" : ""}</option>
                ))}
              </select>
            </div>
            <div className="crear-field">
              <label className="crear-label" htmlFor="precio">Precio por persona ($)</label>
              <input id="precio" name="precio" type="number" className="crear-input" min="0" step="0.01" required placeholder="Ej: 5000" />
            </div>
          </div>

          <div className="crear-tip">
            Coordiná el pago y los detalles del viaje directamente por WhatsApp con tus pasajeros.
          </div>

          <button type="submit" className="btn-publicar" disabled={loading}>
            {loading ? "Publicando..." : "Publicar viaje 🚗"}
          </button>
        </form>
      </div>
    </div>
  );
}
