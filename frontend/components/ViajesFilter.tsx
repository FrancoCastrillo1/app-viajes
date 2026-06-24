"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

interface City { value: string; display: string }

interface ViajesFilterProps {
  cities: City[];
  defaultValues?: { origen?: string; destino?: string; fecha?: string };
}

export default function ViajesFilter({ cities, defaultValues = {} }: ViajesFilterProps) {
  const router = useRouter();
  const [origen, setOrigen] = useState(defaultValues.origen || "");
  const [destino, setDestino] = useState(defaultValues.destino || "");
  const [fecha, setFecha] = useState(defaultValues.fecha || "");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (origen)  params.set("origen", origen);
    if (destino) params.set("destino", destino);
    if (fecha)   params.set("fecha", fecha);
    router.push(`/viajes?${params.toString()}`);
  }

  function handleReset() {
    setOrigen(""); setDestino(""); setFecha("");
    router.push("/viajes");
  }

  return (
    <div className="filter-bar">
      <form onSubmit={handleSubmit}>
        <div className="filter-field">
          <label className="filter-label">Origen</label>
          <select className="filter-select" value={origen} onChange={(e) => setOrigen(e.target.value)}>
            <option value="">Todos</option>
            {cities.map((c) => <option key={c.value} value={c.value}>{c.display}</option>)}
          </select>
        </div>
        <div className="filter-field">
          <label className="filter-label">Destino</label>
          <select className="filter-select" value={destino} onChange={(e) => setDestino(e.target.value)}>
            <option value="">Todos</option>
            {cities.map((c) => <option key={c.value} value={c.value}>{c.display}</option>)}
          </select>
        </div>
        <div className="filter-field">
          <label className="filter-label">Fecha</label>
          <input type="date" className="filter-date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
        </div>
        <button type="submit" className="filter-btn">Buscar</button>
        {(origen || destino || fecha) && (
          <button type="button" className="filter-reset" onClick={handleReset}>Limpiar</button>
        )}
      </form>
    </div>
  );
}
