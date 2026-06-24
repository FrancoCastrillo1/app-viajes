"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import ResenaModal from "./ResenaModal";

interface Viaje {
  id: number;
  origen: string;
  destino: string;
  fecha: string;
  hora: string;
  lugares: number;
  precio: number;
  estado: string;
  reserva_id?: number;
  conductor_nombre?: string;
  conductor_apellido?: string;
  conductor_telefono?: string;
  conductor_id?: number;
}

interface Pasajero {
  viaje_id: number;
  reserva_id: number;
  nombre: string;
  apellido: string;
  telefono: string;
  pasajero_id: number;
}

interface Resena {
  estrellas: number;
  comentario: string;
  created_at: string;
  autor_nombre: string;
  autor_apellido: string;
}

interface PerfilTabsProps {
  viajes: Viaje[];
  misReservas: Viaje[];
  pasajeros: Pasajero[];
  resenas: Resena[];
  resenasEnviadas: string[];
  sessionUserId: number;
}

function EstadoBadge({ estado }: { estado: string }) {
  const cls = estado === "pendiente" ? "estado-pendiente" : estado === "en_viaje" ? "estado-en-viaje" : "estado-finalizado";
  const label = estado === "pendiente" ? "Pendiente" : estado === "en_viaje" ? "En viaje" : "Finalizado";
  const icon = estado === "pendiente" ? "⏳" : estado === "en_viaje" ? "🚗" : "✅";
  return <span className={`estado-badge ${cls}`}>{icon} {label}</span>;
}

function renderStars(n: number) {
  return "★".repeat(n) + "☆".repeat(5 - n);
}

export default function PerfilTabs({ viajes, misReservas, pasajeros, resenas, resenasEnviadas, sessionUserId }: PerfilTabsProps) {
  const [tab, setTab] = useState<"publicaciones" | "reservas" | "resenas">("publicaciones");
  const [modal, setModal] = useState<{ viajeId: number; receptorId: number; nombre: string } | null>(null);
  const router = useRouter();

  async function handleCancelarReserva(reservaId: number) {
    const res = await fetch(`/api/reservas/${reservaId}`, { method: "DELETE" });
    const json = await res.json();
    if (res.ok) { toast.success(json.message); router.refresh(); }
    else toast.error(json.error);
  }

  async function handleCambiarEstado(viajeId: number, estado: string) {
    const res = await fetch(`/api/viaje/${viajeId}/estado`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ estado }),
    });
    const json = await res.json();
    if (res.ok) { toast.success(json.message); router.refresh(); }
    else toast.error(json.error);
  }

  async function handleCancelarViaje(viajeId: number) {
    if (!confirm("¿Cancelar este viaje? Se notificará a todos los pasajeros.")) return;
    const res = await fetch(`/api/viaje/${viajeId}/cancelar`, { method: "DELETE" });
    const json = await res.json();
    if (res.ok) { toast.success("Viaje cancelado."); router.refresh(); }
    else toast.error(json.error);
  }

  const pasajerosPorViaje = pasajeros.reduce<Record<number, Pasajero[]>>((acc, p) => {
    (acc[p.viaje_id] = acc[p.viaje_id] || []).push(p);
    return acc;
  }, {});

  return (
    <>
      {modal && (
        <ResenaModal
          viajeId={modal.viajeId}
          receptorId={modal.receptorId}
          receptorNombre={modal.nombre}
          onClose={() => setModal(null)}
        />
      )}

      <div className="perfil-tabs">
        {(["publicaciones", "reservas", "resenas"] as const).map((t) => (
          <button key={t} className={`tab-btn${tab === t ? " active" : ""}`} onClick={() => setTab(t)}>
            {t === "publicaciones" ? `🚗 Mis viajes (${viajes.length})` :
             t === "reservas" ? `📋 Reservas (${misReservas.length})` :
             `⭐ Reseñas (${resenas.length})`}
          </button>
        ))}
      </div>

      {/* MIS VIAJES */}
      {tab === "publicaciones" && (
        <div>
          {viajes.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🚗</div>
              <p>No publicaste ningún viaje todavía.</p>
              <Link href="/crear-viaje">Publicar mi primer viaje</Link>
            </div>
          ) : viajes.map((v) => (
            <div key={v.id} className="viaje-card">
              <div className="viaje-top">
                <div style={{ flex: 1 }}>
                  <h3 className="viaje-ruta">{v.origen} <span>→</span> {v.destino}</h3>
                  <div className="viaje-meta">
                    <div className="viaje-meta-item">📅 <strong>{v.fecha}</strong></div>
                    <div className="viaje-meta-item">🕐 <strong>{v.hora?.slice(0, 5)}</strong></div>
                    <div className="viaje-meta-item">
                      <span className={`lugares-badge ${v.lugares === 0 ? "agotado" : ""}`}>
                        {v.lugares} lugar{v.lugares !== 1 ? "es" : ""}
                      </span>
                    </div>
                  </div>
                </div>
                <span className="precio-pill">${v.precio}</span>
              </div>

              {/* Pasajeros */}
              {(pasajerosPorViaje[v.id] || []).length > 0 && (
                <div className="pasajeros-list">
                  <h4>Pasajeros</h4>
                  <ul>
                    {(pasajerosPorViaje[v.id] || []).map((p) => (
                      <li key={p.pasajero_id}>
                        <Link href={`/usuario/${p.pasajero_id}`} className="pasajero-link">
                          {p.nombre} {p.apellido}
                        </Link>
                        {v.estado === "finalizado" && !resenasEnviadas.includes(`${v.id}-${p.pasajero_id}`) && (
                          <button
                            className="btn-resena-inline"
                            onClick={() => setModal({ viajeId: v.id, receptorId: p.pasajero_id, nombre: `${p.nombre} ${p.apellido}` })}
                          >
                            ⭐ Calificar
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="estado-row">
                <EstadoBadge estado={v.estado} />
                <div className="estado-controls">
                  {v.estado === "pendiente" && (
                    <button className="btn-estado btn-iniciar" onClick={() => handleCambiarEstado(v.id, "en_viaje")}>▶ Iniciar viaje</button>
                  )}
                  {v.estado === "en_viaje" && (
                    <button className="btn-estado btn-finalizar" onClick={() => handleCambiarEstado(v.id, "finalizado")}>✅ Finalizar viaje</button>
                  )}
                  {v.estado === "pendiente" && (
                    <button className="btn-danger" onClick={() => handleCancelarViaje(v.id)}>✕ Cancelar</button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* MIS RESERVAS */}
      {tab === "reservas" && (
        <div>
          {misReservas.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <p>No tenés reservas activas.</p>
              <Link href="/viajes">Buscar viajes</Link>
            </div>
          ) : misReservas.map((r) => (
            <div key={r.reserva_id} className="reserva-card">
              <h3 className="viaje-ruta">{r.origen} <span>→</span> {r.destino}</h3>
              <div className="viaje-meta">
                <div className="viaje-meta-item">📅 <strong>{r.fecha}</strong></div>
                <div className="viaje-meta-item">🕐 <strong>{r.hora?.slice(0, 5)}</strong></div>
                <div className="viaje-meta-item">💰 <strong>${r.precio}</strong></div>
              </div>
              <div className="conductor-info-box">
                <Link href={`/usuario/${r.conductor_id}`} className="conductor-link">
                  👤 {r.conductor_nombre} {r.conductor_apellido}
                </Link>
                <p style={{ fontSize: "0.85rem", color: "var(--gray-500)", marginTop: "4px" }}>
                  📱 {r.conductor_telefono}
                </p>
              </div>
              <div className="estado-row">
                <EstadoBadge estado={r.estado} />
                <div className="card-actions">
                  {r.estado === "finalizado" && !resenasEnviadas.includes(`${r.id}-${r.conductor_id}`) && (
                    <button
                      className="btn-resena-accion"
                      onClick={() => setModal({ viajeId: r.id, receptorId: r.conductor_id!, nombre: `${r.conductor_nombre} ${r.conductor_apellido}` })}
                    >
                      ⭐ Calificar conductor
                    </button>
                  )}
                  {r.estado === "pendiente" && (
                    <button className="btn-danger" onClick={() => handleCancelarReserva(r.reserva_id!)}>Cancelar reserva</button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* RESEÑAS */}
      {tab === "resenas" && (
        <div>
          {resenas.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">⭐</div>
              <p>Todavía no recibiste reseñas.</p>
            </div>
          ) : resenas.map((r, i) => (
            <div key={i} className="resena-card">
              <div className="resena-header">
                <span className="resena-autor">{r.autor_nombre} {r.autor_apellido}</span>
                <span className="resena-estrellas" style={{ color: "#F59E0B" }}>{renderStars(r.estrellas)}</span>
              </div>
              {r.comentario && <p className="resena-comentario">"{r.comentario}"</p>}
              <span className="resena-fecha">{new Date(r.created_at).toLocaleDateString("es-AR")}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
