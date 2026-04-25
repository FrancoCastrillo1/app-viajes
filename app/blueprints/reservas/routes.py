import threading
import logging

from flask import Blueprint, request, redirect, session, flash

from app.database import get_db
import app.utils.email as email_utils

logger = logging.getLogger(__name__)

reservas_bp = Blueprint("reservas", __name__)


@reservas_bp.route("/reservar/<int:viaje_id>", methods=["POST"])
def reservar(viaje_id):
    if "user_id" not in session:
        return redirect("/login")

    try:
        with get_db() as (conn, cursor):
            cursor.execute(
                "SELECT id FROM reservas WHERE viaje_id = %s AND user_id = %s",
                (viaje_id, session["user_id"]),
            )
            if cursor.fetchone():
                flash("Ya tenés una reserva en este viaje.")
                return redirect("/viajes")

            cursor.execute("""
                SELECT v.*, u.email AS conductor_email, u.nombre AS conductor_nombre
                FROM viajes v
                JOIN users u ON v.user_id = u.id
                WHERE v.id = %s
            """, (viaje_id,))
            viaje = cursor.fetchone()

            if viaje and viaje["user_id"] != session["user_id"] \
                    and viaje["lugares"] > 0 and viaje["estado"] == "pendiente":
                cursor.execute(
                    "INSERT INTO reservas (viaje_id, user_id) VALUES (%s, %s)",
                    (viaje_id, session["user_id"]),
                )
                cursor.execute(
                    "UPDATE viajes SET lugares = lugares - 1 WHERE id = %s AND lugares > 0",
                    (viaje_id,),
                )
                conn.commit()

                origen  = viaje["origen"]
                destino = viaje["destino"]
                fecha   = viaje["fecha"]
                threading.Thread(
                    target=email_utils.enviar_aviso,
                    args=(
                        session["user_email"], "Reserva Confirmada",
                        f"<h2>✅ Reserva confirmada</h2>"
                        f"<p>Tu viaje {origen} → {destino} del {fecha} está reservado.</p>",
                    ),
                    daemon=True,
                ).start()
                threading.Thread(
                    target=email_utils.enviar_aviso,
                    args=(
                        viaje["conductor_email"], "Nuevo Pasajero",
                        f"<h2>🚗 Nuevo pasajero</h2>"
                        f"<p>{session.get('user_nombre')} reservó un lugar en tu viaje "
                        f"{origen} → {destino}.</p>",
                    ),
                    daemon=True,
                ).start()
                flash("¡Viaje reservado exitosamente!")

            elif viaje and viaje["user_id"] == session["user_id"]:
                flash("No podés reservar tu propio viaje.")
            else:
                flash("No se pudo reservar el viaje.")

    except Exception as e:
        logger.error(
            "Error reservando viaje_id=%s user_id=%s: %s",
            viaje_id, session.get("user_id"), e, exc_info=True,
        )
        flash("No se pudo reservar.")

    return redirect("/viajes")


@reservas_bp.route("/viaje/<int:viaje_id>/estado", methods=["POST"])
def cambiar_estado(viaje_id):
    if "user_id" not in session:
        return redirect("/login")

    nuevo_estado = request.form.get("estado")
    if nuevo_estado not in ["pendiente", "en_viaje", "finalizado"]:
        flash("Estado no válido.")
        return redirect("/perfil")

    with get_db() as (conn, cursor):
        cursor.execute("SELECT user_id FROM viajes WHERE id = %s", (viaje_id,))
        viaje = cursor.fetchone()
        if not viaje or viaje["user_id"] != session["user_id"]:
            flash("No tenés permiso para modificar este viaje.")
            return redirect("/perfil")
        cursor.execute(
            "UPDATE viajes SET estado = %s WHERE id = %s",
            (nuevo_estado, viaje_id),
        )
        conn.commit()
    flash("Estado del viaje actualizado.")
    return redirect("/perfil")


@reservas_bp.route("/cancelar_viaje/<int:viaje_id>", methods=["POST"])
def cancelar_viaje(viaje_id):
    if "user_id" not in session:
        return redirect("/login")

    with get_db() as (conn, cursor):
        cursor.execute("SELECT user_id FROM viajes WHERE id = %s", (viaje_id,))
        viaje = cursor.fetchone()
        if not viaje or viaje["user_id"] != session["user_id"]:
            flash("No tenés permiso para cancelar este viaje.")
            return redirect("/perfil")

        cursor.execute(
            "SELECT u.email FROM reservas r JOIN users u ON r.user_id = u.id WHERE r.viaje_id = %s",
            (viaje_id,),
        )
        pasajeros = cursor.fetchall()

        cursor.execute("DELETE FROM reservas WHERE viaje_id = %s", (viaje_id,))
        cursor.execute("DELETE FROM viajes WHERE id = %s", (viaje_id,))
        conn.commit()

    for p in pasajeros:
        threading.Thread(
            target=email_utils.enviar_aviso,
            args=(p["email"], "Viaje Cancelado", "El conductor canceló el viaje."),
            daemon=True,
        ).start()

    return redirect("/perfil")


@reservas_bp.route("/cancelar_reserva/<int:reserva_id>", methods=["POST"])
def cancelar_reserva(reserva_id):
    if "user_id" not in session:
        return redirect("/login")

    with get_db() as (conn, cursor):
        cursor.execute("""
            SELECT r.viaje_id, r.user_id, u.email AS conductor_email
            FROM reservas r
            JOIN viajes v ON r.viaje_id = v.id
            JOIN users u ON v.user_id = u.id
            WHERE r.id = %s
        """, (reserva_id,))
        datos = cursor.fetchone()

        if datos and datos["user_id"] == session["user_id"]:
            cursor.execute("DELETE FROM reservas WHERE id = %s", (reserva_id,))
            cursor.execute(
                "UPDATE viajes SET lugares = lugares + 1 WHERE id = %s",
                (datos["viaje_id"],),
            )
            conn.commit()
            threading.Thread(
                target=email_utils.enviar_aviso,
                args=(
                    datos["conductor_email"],
                    "Lugar liberado",
                    "Un pasajero canceló su lugar en tu viaje.",
                ),
                daemon=True,
            ).start()
            flash("Reserva cancelada.")
        else:
            flash("No podés cancelar esta reserva.")

    return redirect("/perfil")


@reservas_bp.route("/resena/<int:viaje_id>/<int:receptor_id>", methods=["POST"])
def dejar_resena(viaje_id, receptor_id):
    if "user_id" not in session:
        return redirect("/login")

    try:
        estrellas  = int(request.form.get("estrellas", 0))
    except ValueError:
        flash("Calificación inválida.")
        return redirect("/perfil")

    if not (1 <= estrellas <= 5):
        flash("Calificación inválida.")
        return redirect("/perfil")

    comentario = request.form.get("comentario", "").strip()[:500]

    try:
        with get_db() as (conn, cursor):
            cursor.execute(
                "SELECT id, user_id FROM viajes WHERE id = %s AND estado = 'finalizado'",
                (viaje_id,),
            )
            viaje = cursor.fetchone()
            if not viaje:
                flash("Solo podés calificar viajes finalizados.")
                return redirect("/perfil")

            es_conductor = viaje["user_id"] == session["user_id"]
            cursor.execute(
                "SELECT id FROM reservas WHERE viaje_id = %s AND user_id = %s",
                (viaje_id, session["user_id"]),
            )
            es_pasajero = cursor.fetchone() is not None

            if not es_conductor and not es_pasajero:
                flash("Solo podés calificar viajes en los que participaste.")
                return redirect("/perfil")

            if receptor_id == session["user_id"]:
                flash("No podés calificarte a vos mismo.")
                return redirect("/perfil")

            cursor.execute("""
                INSERT INTO resenas (viaje_id, autor_id, receptor_id, estrellas, comentario)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (viaje_id, autor_id, receptor_id) DO NOTHING
            """, (viaje_id, session["user_id"], receptor_id, estrellas, comentario))
            conn.commit()
        flash("¡Reseña enviada!")

    except Exception as e:
        logger.error(
            "Error en reseña viaje_id=%s autor_id=%s: %s",
            viaje_id, session.get("user_id"), e, exc_info=True,
        )
        flash("No se pudo enviar la reseña.")

    return redirect("/perfil")
