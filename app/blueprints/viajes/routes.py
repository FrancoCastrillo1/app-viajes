import logging
from datetime import date

from flask import Blueprint, render_template, request, redirect, session, flash

from app.database import get_db

logger = logging.getLogger(__name__)

viajes_bp = Blueprint("viajes", __name__)


@viajes_bp.route("/viajes")
def viajes():
    with get_db() as (conn, cursor):
        cursor.execute("""
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
            GROUP BY viajes.id, users.nombre, users.apellido, users.telefono,
                     users.avatar_data, users.id
            ORDER BY viajes.fecha, viajes.hora
        """)
        viajes_lista = cursor.fetchall()
    return render_template("viajes.html", viajes=viajes_lista)


@viajes_bp.route("/buscar")
def buscar():
    origen  = request.args.get("origen", "")
    destino = request.args.get("destino", "")
    fecha   = request.args.get("fecha", "")

    query  = """
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
    """
    params = []
    if origen:
        query += " AND viajes.origen ILIKE %s"
        params.append(f"%{origen}%")
    if destino:
        query += " AND viajes.destino ILIKE %s"
        params.append(f"%{destino}%")
    if fecha:
        query += " AND viajes.fecha = %s"
        params.append(fecha)
    query += """
        GROUP BY viajes.id, users.nombre, users.apellido, users.telefono,
                 users.avatar_data, users.id
        ORDER BY viajes.fecha ASC
    """

    with get_db() as (conn, cursor):
        cursor.execute(query, params)
        resultados = cursor.fetchall()
    return render_template("viajes.html", viajes=resultados, busqueda=True)


@viajes_bp.route("/viajes/<int:viaje_id>")
def ver_viaje(viaje_id):
    with get_db() as (conn, cursor):
        cursor.execute("""
            SELECT viajes.*, users.nombre, users.apellido, users.telefono,
                   users.id AS conductor_id, users.avatar_data,
                   COALESCE(ROUND(AVG(r.estrellas)::numeric, 1), 0) AS promedio_conductor,
                   COUNT(r.id) AS total_resenas
            FROM viajes
            JOIN users ON viajes.user_id = users.id
            LEFT JOIN resenas r ON r.receptor_id = users.id
            WHERE viajes.id = %s
            GROUP BY viajes.id, users.nombre, users.apellido, users.telefono,
                     users.id, users.avatar_data
        """, (viaje_id,))
        viaje = cursor.fetchone()
    if not viaje:
        return redirect("/viajes")
    return render_template("ver_viaje.html", viaje=viaje)


@viajes_bp.route("/crear_viaje", methods=["GET", "POST"])
def crear_viaje():
    if "user_id" not in session:
        return redirect("/login")

    with get_db() as (conn, cursor):
        cursor.execute(
            "SELECT verificado FROM users WHERE id = %s",
            (session["user_id"],),
        )
        user_status = cursor.fetchone()

    if not user_status or not user_status["verificado"]:
        flash("Debés verificar tu cuenta antes de publicar un viaje.")
        return redirect("/verificar")

    fecha_hoy = date.today().isoformat()

    if request.method == "POST":
        origen    = request.form.get("origen", "")
        destino   = request.form.get("destino", "")
        encuentro = request.form.get("encuentro", "").strip()
        fecha     = request.form.get("fecha", "")
        hora      = request.form.get("hora", "")

        if origen == destino:
            flash("El origen y el destino no pueden ser iguales.")
            return redirect("/crear_viaje")

        try:
            precio  = float(request.form["precio"])
            lugares = int(request.form["lugares"])
            if precio < 0 or not (1 <= lugares <= 8):
                raise ValueError
        except (ValueError, KeyError):
            flash("Datos del viaje inválidos.")
            return redirect("/crear_viaje")

        try:
            with get_db() as (conn, cursor):
                cursor.execute("""
                    INSERT INTO viajes
                        (user_id, origen, destino, encuentro, fecha, hora, lugares, precio, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')
                """, (session["user_id"], origen, destino, encuentro,
                      fecha, hora, lugares, precio))
                conn.commit()
            return redirect("/perfil")
        except Exception as e:
            logger.error("Error creando viaje user_id=%s: %s", session.get("user_id"), e, exc_info=True)
            flash("Hubo un error al publicar el viaje.")
            return redirect("/crear_viaje")

    return render_template("crear_viaje.html", fecha_hoy=fecha_hoy)
