import logging

from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash

from app.database import get_db
from app.utils.images import process_avatar

logger = logging.getLogger(__name__)

usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/perfil")
def perfil():
    if "user_id" not in session:
        return redirect("/login")

    with get_db() as (conn, cursor):
        cursor.execute(
            "SELECT nombre, apellido, telefono, email, avatar_data FROM users WHERE id = %s",
            (session["user_id"],),
        )
        user = cursor.fetchone()

        cursor.execute("""
            SELECT viajes.*, reservas.id AS reserva_id,
                   conductor.nombre    AS conductor_nombre,
                   conductor.apellido  AS conductor_apellido,
                   conductor.telefono  AS conductor_telefono,
                   conductor.id        AS conductor_id
            FROM reservas
            JOIN viajes ON reservas.viaje_id = viajes.id
            JOIN users AS conductor ON viajes.user_id = conductor.id
            WHERE reservas.user_id = %s
            ORDER BY viajes.fecha DESC
        """, (session["user_id"],))
        mis_reservas = cursor.fetchall()

        cursor.execute(
            "SELECT * FROM viajes WHERE user_id = %s ORDER BY fecha DESC",
            (session["user_id"],),
        )
        mis_publicaciones = cursor.fetchall()

        cursor.execute("""
            SELECT reservas.viaje_id,
                   users.nombre, users.apellido, users.telefono,
                   users.id AS pasajero_id
            FROM reservas
            JOIN users ON reservas.user_id = users.id
            WHERE reservas.viaje_id IN (
                SELECT id FROM viajes WHERE user_id = %s
            )
        """, (session["user_id"],))
        pasajeros = cursor.fetchall()

        cursor.execute("""
            SELECT r.estrellas, r.comentario, r.created_at,
                   u.nombre AS autor_nombre, u.apellido AS autor_apellido
            FROM resenas r
            JOIN users u ON r.autor_id = u.id
            WHERE r.receptor_id = %s
            ORDER BY r.created_at DESC
        """, (session["user_id"],))
        resenas_recibidas = cursor.fetchall()

        cursor.execute(
            "SELECT viaje_id, receptor_id FROM resenas WHERE autor_id = %s",
            (session["user_id"],),
        )
        resenas_enviadas = {(r["viaje_id"], r["receptor_id"]) for r in cursor.fetchall()}

    promedio = None
    if resenas_recibidas:
        promedio = round(
            sum(r["estrellas"] for r in resenas_recibidas) / len(resenas_recibidas), 1
        )

    return render_template(
        "perfil.html",
        user=user,
        mis_reservas=mis_reservas,
        viajes=mis_publicaciones,
        reservas=pasajeros,
        cantidad_viajes=len(mis_publicaciones),
        resenas=resenas_recibidas,
        promedio=promedio,
        resenas_enviadas=resenas_enviadas,
        es_propio=True,
    )


@usuarios_bp.route("/editar_perfil", methods=["GET", "POST"])
def editar_perfil():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        nombre         = request.form.get("nombre", "").strip()
        apellido       = request.form.get("apellido", "").strip()
        nueva_password = request.form.get("nueva_password", "").strip()
        avatar_file    = request.files.get("avatar")

        try:
            avatar_data = None
            if avatar_file and avatar_file.filename:
                file_bytes = avatar_file.read()
                ext        = avatar_file.filename.rsplit(".", 1)[-1].lower()
                avatar_data, error = process_avatar(file_bytes, ext)
                if error:
                    flash(error)
                    return redirect("/editar_perfil")

            with get_db() as (conn, cursor):
                if nueva_password:
                    if len(nueva_password) < 6:
                        flash("La contraseña debe tener al menos 6 caracteres.")
                        return redirect("/editar_perfil")
                    hashed = generate_password_hash(nueva_password)
                    if avatar_data:
                        cursor.execute(
                            "UPDATE users SET nombre=%s, apellido=%s, password=%s, avatar_data=%s WHERE id=%s",
                            (nombre, apellido, hashed, avatar_data, session["user_id"]),
                        )
                    else:
                        cursor.execute(
                            "UPDATE users SET nombre=%s, apellido=%s, password=%s WHERE id=%s",
                            (nombre, apellido, hashed, session["user_id"]),
                        )
                else:
                    if avatar_data:
                        cursor.execute(
                            "UPDATE users SET nombre=%s, apellido=%s, avatar_data=%s WHERE id=%s",
                            (nombre, apellido, avatar_data, session["user_id"]),
                        )
                    else:
                        cursor.execute(
                            "UPDATE users SET nombre=%s, apellido=%s WHERE id=%s",
                            (nombre, apellido, session["user_id"]),
                        )
                conn.commit()

            session["user_nombre"] = nombre
            flash("¡Perfil actualizado con éxito!")
            return redirect("/perfil")

        except Exception as e:
            logger.error(
                "Error editando perfil user_id=%s: %s", session.get("user_id"), e, exc_info=True
            )
            flash("Hubo un error al actualizar tu perfil.")
            return redirect("/editar_perfil")

    with get_db() as (conn, cursor):
        cursor.execute(
            "SELECT nombre, apellido, email, telefono, avatar_data FROM users WHERE id = %s",
            (session["user_id"],),
        )
        user = cursor.fetchone()
    return render_template("editar_perfil.html", user=user)


@usuarios_bp.route("/usuario/<int:user_id>")
def perfil_publico(user_id):
    with get_db() as (conn, cursor):
        cursor.execute(
            "SELECT id, nombre, apellido, avatar_data FROM users WHERE id = %s",
            (user_id,),
        )
        user = cursor.fetchone()
        if not user:
            flash("Usuario no encontrado.")
            return redirect("/viajes")

        cursor.execute(
            "SELECT * FROM viajes WHERE user_id = %s ORDER BY fecha DESC",
            (user_id,),
        )
        viajes_usuario = cursor.fetchall()

        cursor.execute("""
            SELECT r.estrellas, r.comentario, r.created_at,
                   u.nombre AS autor_nombre, u.apellido AS autor_apellido
            FROM resenas r
            JOIN users u ON r.autor_id = u.id
            WHERE r.receptor_id = %s
            ORDER BY r.created_at DESC
        """, (user_id,))
        resenas = cursor.fetchall()

    promedio = None
    if resenas:
        promedio = round(sum(r["estrellas"] for r in resenas) / len(resenas), 1)

    return render_template(
        "perfil_publico.html",
        user=user,
        viajes=viajes_usuario,
        resenas=resenas,
        promedio=promedio,
    )
