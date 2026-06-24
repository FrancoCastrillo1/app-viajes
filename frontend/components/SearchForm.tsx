"use client";

import { useRouter } from "next/navigation";

interface City { value: string; display: string }

export default function SearchForm({ cities }: { cities: City[] }) {
  const router = useRouter();

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const get = (name: string) => (form.elements.namedItem(name) as HTMLSelectElement | HTMLInputElement).value;
    const params = new URLSearchParams();
    const origen  = get("origen");
    const destino = get("destino");
    const fecha   = get("fecha");
    if (origen)  params.set("origen", origen);
    if (destino) params.set("destino", destino);
    if (fecha)   params.set("fecha", fecha);
    router.push(`/viajes?${params.toString()}`);
  }

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="search-row">
        <div className="field-group">
          <label className="field-label">Origen</label>
          <div className="select-wrap">
            <select name="origen" required>
              <option value="" disabled>¿De dónde salís?</option>
              {cities.map((c) => <option key={c.value} value={c.value}>{c.display}</option>)}
            </select>
            <span className="select-icon">↓</span>
          </div>
        </div>
        <div className="route-arrow">→</div>
        <div className="field-group">
          <label className="field-label">Destino</label>
          <div className="select-wrap">
            <select name="destino" required>
              <option value="" disabled>¿A dónde vas?</option>
              {cities.map((c) => <option key={c.value} value={c.value}>{c.display}</option>)}
            </select>
            <span className="select-icon">↓</span>
          </div>
        </div>
        <div className="field-group field-date">
          <label className="field-label">Fecha (opcional)</label>
          <input type="date" name="fecha" className="date-input" />
        </div>
      </div>
      <button type="submit" className="btn-search">Buscar viaje 🔍</button>
    </form>
  );
}
