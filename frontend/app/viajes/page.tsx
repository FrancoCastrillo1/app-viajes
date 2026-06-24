import { Suspense } from "react";
import { getSession } from "@/lib/auth";
import sql from "@/lib/db";
import { CITIES } from "@/lib/cities";
import ViajeCard, { Viaje } from "@/components/ViajeCard";
import ViajesFilter from "@/components/ViajesFilter";

interface SearchParams {
  origen?: string;
  destino?: string;
  fecha?: string;
  busqueda?: string;
}

async function getViajes(searchParams: SearchParams): Promise<Viaje[]> {
  const { origen, destino, fecha } = searchParams;
  const isBusqueda = origen || destino || fecha;

  if (isBusqueda) {
    return sql`
      SELECT viajes.*, users.nombre, users.apellido, users.telefono, users.avatar_data,
             users.id AS conductor_id,
             COALESCE(ROUND(AVG(r.estrellas)::numeric, 1), 0) AS promedio_conductor,
             COUNT(r.id) AS total_resenas
      FROM viajes
      JOIN users ON viajes.user_id = users.id
      LEFT JOIN resenas r ON r.receptor_id = users.id
      WHERE viajes.estado = 'pendiente'
        AND viajes.lugares > 0
        AND (viajes.fecha + viajes.hora)::timestamp > NOW()
        ${origen  ? sql`AND viajes.origen  ILIKE ${"%" + origen  + "%"}` : sql``}
        ${destino ? sql`AND viajes.destino ILIKE ${"%" + destino + "%"}` : sql``}
        ${fecha   ? sql`AND viajes.fecha = ${fecha}`                      : sql``}
      GROUP BY viajes.id, users.nombre, users.apellido, users.telefono, users.avatar_data, users.id
      ORDER BY viajes.fecha ASC
    ` as unknown as Viaje[];
  }

  return sql`
    SELECT viajes.*, users.nombre, users.apellido, users.telefono, users.avatar_data,
           users.id AS conductor_id,
           COALESCE(ROUND(AVG(r.estrellas)::numeric, 1), 0) AS promedio_conductor,
           COUNT(r.id) AS total_resenas
    FROM viajes
    JOIN users ON viajes.user_id = users.id
    LEFT JOIN resenas r ON r.receptor_id = users.id
    WHERE viajes.lugares > 0
      AND viajes.estado = 'pendiente'
      AND (viajes.fecha + viajes.hora)::timestamp > NOW()
    GROUP BY viajes.id, users.nombre, users.apellido, users.telefono, users.avatar_data, users.id
    ORDER BY viajes.fecha, viajes.hora
  ` as unknown as Viaje[];
}

export default async function ViajesPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const session = await getSession();
  const viajes = await getViajes(params);
  const isBusqueda = !!(params.origen || params.destino || params.fecha);

  return (
    <div className="viajes-page">
      <div className="viajes-header">
        <h1>{isBusqueda ? "Resultados de búsqueda" : "Viajes disponibles"}</h1>
        <p>{isBusqueda ? `${viajes.length} viaje${viajes.length !== 1 ? "s" : ""} encontrado${viajes.length !== 1 ? "s" : ""}` : "Encontrá tu próximo viaje compartido"}</p>
      </div>

      <Suspense fallback={null}>
        <ViajesFilter cities={CITIES} defaultValues={params} />
      </Suspense>

      {viajes.length === 0 ? (
        <div className="empty-viajes">
          <div className="icon">🚗</div>
          <h3>{isBusqueda ? "No encontramos viajes para esa búsqueda" : "No hay viajes disponibles por ahora"}</h3>
          <p>{isBusqueda ? "Probá con otra fecha o ciudad." : "Sé el primero en publicar un viaje."}</p>
          {isBusqueda ? (
            <a href="/viajes">Ver todos los viajes</a>
          ) : (
            <a href="/crear-viaje">Publicar un viaje</a>
          )}
        </div>
      ) : (
        viajes.map((v) => (
          <ViajeCard key={v.id} viaje={v} sessionUserId={session.userId} />
        ))
      )}
    </div>
  );
}
