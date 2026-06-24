import { redirect } from "next/navigation";
import sql from "@/lib/db";

function renderStars(n: number) {
  return "★".repeat(Math.round(n)) + "☆".repeat(5 - Math.round(n));
}

export default async function PerfilPublicoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const userId = parseInt(id);

  const [user] = await sql`
    SELECT id, nombre, apellido, avatar_data FROM users WHERE id = ${userId}
  `;
  if (!user) redirect("/viajes");

  const viajes = await sql`
    SELECT * FROM viajes WHERE user_id = ${userId} ORDER BY fecha DESC
  `;

  const resenas = await sql`
    SELECT r.estrellas, r.comentario, r.created_at,
           u.nombre AS autor_nombre, u.apellido AS autor_apellido
    FROM resenas r
    JOIN users u ON r.autor_id = u.id
    WHERE r.receptor_id = ${userId}
    ORDER BY r.created_at DESC
  `;

  const promedio =
    resenas.length > 0
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ? ((resenas as any[]).reduce((sum: number, r) => sum + r.estrellas, 0) / resenas.length).toFixed(1)
      : null;

  return (
    <div className="perfil-page">
      <div className="perfil-header">
        <div className="perfil-avatar-wrap">
          {user.avatar_data ? (
            <img src={user.avatar_data} alt="Avatar" className="perfil-avatar-img" />
          ) : (
            <div className="perfil-avatar">{user.nombre?.[0]?.toUpperCase()}</div>
          )}
        </div>

        <div className="perfil-info-main">
          <h1 className="perfil-name">{user.nombre} {user.apellido}</h1>
          {promedio && (
            <div className="perfil-rating">
              <span className="stars-static" style={{ color: "#F59E0B" }}>{renderStars(parseFloat(promedio))}</span>
              <span className="rating-num">{promedio}</span>
              <span className="rating-count">({resenas.length} reseña{resenas.length !== 1 ? "s" : ""})</span>
            </div>
          )}
        </div>

        <div className="stat-badges">
          <div className="stat-badge">
            <span className="stat-num">{viajes.length}</span>
            <span className="stat-label">Viajes</span>
          </div>
          <div className="stat-badge">
            <span className="stat-num">{resenas.length}</span>
            <span className="stat-label">Reseñas</span>
          </div>
        </div>
      </div>

      {viajes.length > 0 && (
        <>
          <h2 className="section-title">🚗 Viajes publicados</h2>
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          {(viajes as any[]).map((v) => (
            <div key={v.id} className="viaje-card">
              <div className="viaje-top">
                <div style={{ flex: 1 }}>
                  <h3 className="viaje-ruta">{v.origen} <span>→</span> {v.destino}</h3>
                  <div className="viaje-meta">
                    <div className="viaje-meta-item">📅 <strong>{v.fecha}</strong></div>
                    <div className="viaje-meta-item">🕐 <strong>{v.hora?.slice(0, 5)}</strong></div>
                  </div>
                </div>
                <span className="precio-pill">${v.precio}</span>
              </div>
            </div>
          ))}
        </>
      )}

      {resenas.length > 0 && (
        <>
          <h2 className="section-title">⭐ Reseñas recibidas</h2>
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          {(resenas as any[]).map((r, i: number) => (
            <div key={i} className="resena-card">
              <div className="resena-header">
                <span className="resena-autor">{r.autor_nombre} {r.autor_apellido}</span>
                <span className="resena-estrellas" style={{ color: "#F59E0B" }}>{"★".repeat(r.estrellas)}{"☆".repeat(5 - r.estrellas)}</span>
              </div>
              {r.comentario && <p className="resena-comentario">"{r.comentario}"</p>}
              <span className="resena-fecha">{new Date(r.created_at).toLocaleDateString("es-AR")}</span>
            </div>
          ))}
        </>
      )}

      {viajes.length === 0 && resenas.length === 0 && (
        <div className="empty-state" style={{ marginTop: "24px" }}>
          <div className="empty-icon">👤</div>
          <p>Este usuario todavía no tiene actividad.</p>
        </div>
      )}
    </div>
  );
}
