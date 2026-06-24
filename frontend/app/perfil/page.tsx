import { redirect } from "next/navigation";
import Link from "next/link";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";
import PerfilTabs from "@/components/PerfilTabs";

function renderStars(n: number) {
  return "★".repeat(Math.round(n)) + "☆".repeat(5 - Math.round(n));
}

export default async function PerfilPage() {
  const session = await getSession();
  if (!session.userId) redirect("/login");

  const [user] = await sql`
    SELECT nombre, apellido, telefono, email, avatar_data FROM users WHERE id = ${session.userId}
  `;

  const misReservas = await sql`
    SELECT viajes.*, reservas.id AS reserva_id,
           conductor.nombre AS conductor_nombre, conductor.apellido AS conductor_apellido,
           conductor.telefono AS conductor_telefono, conductor.id AS conductor_id
    FROM reservas
    JOIN viajes ON reservas.viaje_id = viajes.id
    JOIN users AS conductor ON viajes.user_id = conductor.id
    WHERE reservas.user_id = ${session.userId}
    ORDER BY viajes.fecha DESC
  `;

  const misPublicaciones = await sql`
    SELECT * FROM viajes WHERE user_id = ${session.userId} ORDER BY fecha DESC
  `;

  const pasajeros = await sql`
    SELECT reservas.viaje_id, reservas.id AS reserva_id,
           users.nombre, users.apellido, users.telefono, users.id AS pasajero_id
    FROM reservas
    JOIN users ON reservas.user_id = users.id
    WHERE reservas.viaje_id IN (SELECT id FROM viajes WHERE user_id = ${session.userId})
  `;

  const resenasRecibidas = await sql`
    SELECT r.estrellas, r.comentario, r.created_at,
           u.nombre AS autor_nombre, u.apellido AS autor_apellido
    FROM resenas r
    JOIN users u ON r.autor_id = u.id
    WHERE r.receptor_id = ${session.userId}
    ORDER BY r.created_at DESC
  `;

  const resenasEnviadasRaw = await sql`
    SELECT viaje_id, receptor_id FROM resenas WHERE autor_id = ${session.userId}
  `;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const resenasEnviadas = (resenasEnviadasRaw as any[]).map(
    (r) => `${r.viaje_id}-${r.receptor_id}`
  );

  const promedio =
    resenasRecibidas.length > 0
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ? ((resenasRecibidas as any[]).reduce((sum: number, r) => sum + r.estrellas, 0) / resenasRecibidas.length).toFixed(1)
      : null;

  return (
    <div className="perfil-page">
      {/* Header */}
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
              <span className="rating-count">({resenasRecibidas.length} reseña{resenasRecibidas.length !== 1 ? "s" : ""})</span>
            </div>
          )}
          {!promedio && <p className="no-rating-msg">Sin reseñas todavía</p>}
          <div className="perfil-meta">
            <div className="perfil-meta-item">✉️ {user.email}</div>
            {user.telefono && <div className="perfil-meta-item">📱 {user.telefono}</div>}
          </div>
        </div>

        <div className="perfil-header-right">
          <div className="stat-badges">
            <div className="stat-badge">
              <span className="stat-num">{misPublicaciones.length}</span>
              <span className="stat-label">Viajes</span>
            </div>
            <div className="stat-badge">
              <span className="stat-num">{resenasRecibidas.length}</span>
              <span className="stat-label">Reseñas</span>
            </div>
          </div>
          <Link href="/editar-perfil" className="btn-editar-perfil">✏️ Editar perfil</Link>
        </div>
      </div>

      <PerfilTabs
        viajes={misPublicaciones as never}
        misReservas={misReservas as never}
        pasajeros={pasajeros as never}
        resenas={resenasRecibidas as never}
        resenasEnviadas={resenasEnviadas}
        sessionUserId={session.userId}
      />
    </div>
  );
}
