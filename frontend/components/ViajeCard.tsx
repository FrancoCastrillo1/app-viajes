import Link from "next/link";

export interface Viaje {
  id: number;
  origen: string;
  destino: string;
  fecha: string;
  hora: string;
  lugares: number;
  precio: number;
  encuentro: string;
  estado: "pendiente" | "en_viaje" | "finalizado";
  user_id: number;
  nombre: string;
  apellido: string;
  telefono: string;
  avatar_data?: string;
  conductor_id: number;
  promedio_conductor: number;
  total_resenas: number;
}

function renderStars(promedio: number) {
  const full = Math.floor(promedio);
  const half = promedio - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return "★".repeat(full) + (half ? "½" : "") + "☆".repeat(empty);
}

interface ViajeCardProps {
  viaje: Viaje;
  sessionUserId?: number;
  showReservar?: boolean;
}

export default function ViajeCard({ viaje, sessionUserId, showReservar = true }: ViajeCardProps) {
  const esMio = sessionUserId === viaje.user_id;
  const waLink = `https://wa.me/${viaje.telefono?.replace(/\D/g, "")}?text=${encodeURIComponent(`Hola ${viaje.nombre}, vi tu viaje en Ruta Compartida ${viaje.origen} → ${viaje.destino} el ${viaje.fecha}`)}`;

  return (
    <div className="viaje-card">
      <div className="viaje-top">
        <div style={{ flex: 1 }}>
          <h2 className="viaje-ruta">
            {viaje.origen}
            <span className="arrow"> → </span>
            {viaje.destino}
          </h2>
          <div className="viaje-meta">
            <div className="viaje-meta-item">📅 <strong>{viaje.fecha}</strong></div>
            <div className="viaje-meta-item">🕐 <strong>{viaje.hora?.slice(0, 5)}</strong></div>
            <div className="viaje-meta-item">
              <span className={`lugares-badge ${viaje.lugares === 0 ? "agotado" : ""}`}>
                {viaje.lugares === 0 ? "Sin lugares" : `${viaje.lugares} lugar${viaje.lugares !== 1 ? "es" : ""}`}
              </span>
            </div>
          </div>
          {viaje.encuentro && (
            <div className="viaje-detail">📍 Punto de encuentro: <strong>{viaje.encuentro}</strong></div>
          )}
        </div>
        <span className="precio-pill">${viaje.precio}</span>
      </div>

      <hr className="viaje-divider" />

      <div className="viaje-bottom">
        <div>
          <p className="conductor-label">Conductor</p>
          <Link href={`/usuario/${viaje.conductor_id}`} className="conductor-name conductor-name-link">
            {viaje.avatar_data ? (
              <img src={viaje.avatar_data} alt="" className="conductor-avatar-sm" />
            ) : (
              <span>👤</span>
            )}
            {viaje.nombre} {viaje.apellido}
          </Link>
          {viaje.total_resenas > 0 && (
            <div className="viaje-conductor-rating">
              <span className="mini-stars">{renderStars(viaje.promedio_conductor)}</span>
              <span>{viaje.promedio_conductor}</span>
              <span className="review-count">({viaje.total_resenas})</span>
            </div>
          )}
        </div>

        <div className="card-actions">
          <a href={waLink} target="_blank" rel="noopener noreferrer" className="btn-whatsapp">
            📱 WhatsApp
          </a>
          {showReservar && !esMio && viaje.lugares > 0 && sessionUserId && (
            <ReservarBtn viajeId={viaje.id} />
          )}
          {!sessionUserId && viaje.lugares > 0 && (
            <Link href="/login" className="btn-reservar">Reservar lugar</Link>
          )}
          {viaje.lugares === 0 && (
            <div className="agotado-msg">Sin lugares disponibles</div>
          )}
        </div>
      </div>
    </div>
  );
}

function ReservarBtn({ viajeId }: { viajeId: number }) {
  return (
    <form action={`/api/reservas`} method="POST" style={{ display: "inline" }}>
      <input type="hidden" name="viajeId" value={viajeId} />
      <button type="submit" className="btn-reservar">Reservar lugar</button>
    </form>
  );
}
