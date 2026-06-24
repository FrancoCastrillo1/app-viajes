import { redirect } from "next/navigation";
import Link from "next/link";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";
import ReservarClientBtn from "@/components/ReservarClientBtn";

function renderStars(promedio: number) {
  const full = Math.floor(promedio);
  const half = promedio - full >= 0.5 ? 1 : 0;
  return "★".repeat(full) + (half ? "½" : "") + "☆".repeat(5 - full - half);
}

export default async function VerViajePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const session = await getSession();

  const [viaje] = await sql`
    SELECT viajes.*, users.nombre, users.apellido, users.telefono,
           users.id AS conductor_id, users.avatar_data,
           COALESCE(ROUND(AVG(r.estrellas)::numeric, 1), 0) AS promedio_conductor,
           COUNT(r.id) AS total_resenas
    FROM viajes
    JOIN users ON viajes.user_id = users.id
    LEFT JOIN resenas r ON r.receptor_id = users.id
    WHERE viajes.id = ${parseInt(id)}
    GROUP BY viajes.id, users.nombre, users.apellido, users.telefono, users.id, users.avatar_data
  `;

  if (!viaje) redirect("/viajes");

  const esMio = session.userId === viaje.conductor_id;
  const waLink = `https://wa.me/${viaje.telefono?.replace(/\D/g, "")}?text=${encodeURIComponent(`Hola ${viaje.nombre}, vi tu viaje en Ruta Compartida ${viaje.origen} → ${viaje.destino} el ${viaje.fecha}`)}`;

  return (
    <div className="detalle-wrapper">
      <div className="detalle-card">
        <div className="detalle-header">
          <h1>
            {viaje.origen}
            <span className="arrow"> → </span>
            {viaje.destino}
          </h1>
          <p>Detalle del viaje compartido</p>
        </div>

        <div className="viaje-meta" style={{ marginBottom: "20px" }}>
          <div className="viaje-meta-item">📅 <strong>{viaje.fecha}</strong></div>
          <div className="viaje-meta-item">🕐 <strong>{viaje.hora?.slice(0, 5)}</strong></div>
          <div className="viaje-meta-item">
            <span className={`lugares-badge ${viaje.lugares === 0 ? "agotado" : ""}`}>
              {viaje.lugares === 0 ? "Sin lugares" : `${viaje.lugares} lugar${viaje.lugares !== 1 ? "es" : ""}`}
            </span>
          </div>
          <div className="viaje-meta-item">💰 <strong>${viaje.precio}</strong></div>
        </div>

        {viaje.encuentro && (
          <div className="conductor-info">
            📍 <strong>Punto de encuentro:</strong> {viaje.encuentro}
          </div>
        )}

        <div className="conductor-card">
          {viaje.avatar_data ? (
            <img src={viaje.avatar_data} alt="" className="conductor-avatar-ph" style={{ objectFit: "cover" }} />
          ) : (
            <div className="conductor-avatar-ph">{viaje.nombre?.[0]}</div>
          )}
          <div>
            <Link href={`/usuario/${viaje.conductor_id}`} className="conductor-card-name conductor-name-link">
              {viaje.nombre} {viaje.apellido}
            </Link>
            <p className="conductor-card-tel">📱 {viaje.telefono}</p>
            {viaje.total_resenas > 0 && (
              <div className="viaje-conductor-rating">
                <span className="mini-stars">{renderStars(viaje.promedio_conductor)}</span>
                <span>{viaje.promedio_conductor}</span>
                <span className="review-count">({viaje.total_resenas} reseñas)</span>
              </div>
            )}
          </div>
        </div>

        <div className="card-actions" style={{ marginTop: "24px" }}>
          <a href={waLink} target="_blank" rel="noopener noreferrer" className="btn-whatsapp">
            📱 Contactar por WhatsApp
          </a>
          {!esMio && viaje.lugares > 0 && session.userId && (
            <ReservarClientBtn viajeId={viaje.id} />
          )}
          {!session.userId && viaje.lugares > 0 && (
            <Link href="/login" className="btn-reservar">Reservar lugar</Link>
          )}
          {viaje.lugares === 0 && (
            <div className="agotado-msg">Sin lugares disponibles</div>
          )}
        </div>

        <div style={{ marginTop: "20px" }}>
          <Link href="/viajes" style={{ color: "var(--primary)", fontWeight: 600, fontSize: "0.9rem" }}>
            ← Volver a todos los viajes
          </Link>
        </div>
      </div>
    </div>
  );
}
