from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import date
import requests
import random
import base64

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_fallback_key_cambiar_en_produccion")

def get_db_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")

def run_migrations():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_data TEXT;")
        cursor.execute("ALTER TABLE viajes ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'pendiente';")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resenas (
                id SERIAL PRIMARY KEY,
                viaje_id INTEGER NOT NULL REFERENCES viajes(id) ON DELETE CASCADE,
                autor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                receptor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                estrellas INTEGER NOT NULL CHECK (estrellas BETWEEN 1 AND 5),
                comentario TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(viaje_id, autor_id, receptor_id)
            );
        """)
        conn.commit()
        print("✅ Migraciones ejecutadas correctamente.")
    except Exception as e:
        conn.rollback()
        print(f"⚠️ Error en migraciones: {e}")
    finally:
        cursor.close()
        conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre   = request.form["nombre"].strip()
        apellido = request.form["apellido"].strip()
        telefono = request.form["telefono"].strip()
        email    = request.form["email"].strip().lower()
        password = generate_password_hash(request.form["password"])
        codigo   = str(random.randint(100000, 999999))
        conn   = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                INSERT INTO users (nombre, apellido, telefono, email, password, codigo_verificacion, verificado)
                VALUES (%s, %s, %s, %s, %s, %s, FALSE) RETURNING id
            """, (nombre, apellido, telefono, email, password, codigo))
            new_user = cursor.fetchone()
            conn.commit()
            enviar_mail_verificacion(email, codigo)
            session["user_id"]     = new_user["id"]
            session["user_email"]  = email
            session["user_nombre"] = nombre
            return redirect("/verificar")
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("Este email ya está registrado. Por favor, iniciá sesión.")
            return redirect("/register")
        except Exception as e:
            conn.rollback()
            print(f"Error en registro: {e}")
            flash("Hubo un error al procesar tu registro.")
            return redirect("/register")
        finally:
            cursor.close()
            conn.close()
    return render_template("register.html")

def enviar_mail_verificacion(email_destino, codigo):
    api_key = os.environ.get("RESEND_API_KEY")
    url     = "https://api.resend.com/emails"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "from": "Ruta Compartida <verificacion@rutacompartida.com.ar>",
        "to": email_destino,
        "subject": "Tu código de verificación - Ruta Compartida",
        "html": f"""<div style="font-family:sans-serif;text-align:center;border:2px solid #E76F51;padding:20px;border-radius:15px;max-width:400px;margin:auto;">
            <h2 style="color:#E76F51;">¡Hola! 👋</h2>
            <p>Tu código de seguridad para <strong>Ruta Compartida</strong>:</p>
            <div style="background:#FFEDD5;color:#E76F51;padding:15px;font-size:2rem;font-weight:bold;border-radius:10px;margin:20px 0;letter-spacing:5px;">{codigo}</div>
            <p style="color:#666;font-size:0.9rem;">Si no solicitaste este código, ignorá este mensaje.</p>
            <p style="font-size:0.8rem;color:#999;">© 2026 Ruta Compartida</p></div>"""
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error enviando mail: {e}")
        return False

@app.route("/verificar", methods=["GET", "POST"])
def verificar():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        codigo_ingresado = request.form["codigo"]
        conn   = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT codigo_verificacion FROM users WHERE id = %s", (session["user_id"],))
            user = cursor.fetchone()
            if user and user["codigo_verificacion"] == codigo_ingresado:
                cursor.execute("UPDATE users SET verificado = TRUE WHERE id = %s", (session["user_id"],))
                conn.commit()
                flash("¡Cuenta verificada con éxito!")
                return redirect("/viajes")
            else:
                flash("Código incorrecto. Intentá de nuevo.")
        finally:
            cursor.close()
            conn.close()
    return render_template("verificar.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn   = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"]     = user["id"]
            session["user_email"]  = user["email"]
            session["user_nombre"] = user["nombre"]
            flash("¡Bienvenido de nuevo!")
            return redirect("/index")
        else:
            flash("Email o contraseña incorrectos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/perfil")
def perfil():
    if "user_id" not in session:
        return redirect("/login")
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT nombre, apellido, telefono, email, avatar_data FROM users WHERE id = %s", (session["user_id"],))
        user = cursor.fetchone()
        cursor.execute("""
            SELECT viajes.*, reservas.id AS reserva_id,
                   conductor.nombre AS conductor_nombre, conductor.apellido AS conductor_apellido,
                   conductor.telefono AS conductor_telefono, conductor.id AS conductor_id
            FROM reservas
            JOIN viajes ON reservas.viaje_id = viajes.id
            JOIN users AS conductor ON viajes.user_id = conductor.id
            WHERE reservas.user_id = %s ORDER BY viajes.fecha DESC
        """, (session["user_id"],))
        mis_reservas = cursor.fetchall()
        cursor.execute("SELECT * FROM viajes WHERE user_id = %s ORDER BY fecha DESC", (session["user_id"],))
        mis_publicaciones = cursor.fetchall()
        cursor.execute("""
            SELECT reservas.viaje_id, users.nombre, users.apellido, users.telefono, users.id AS pasajero_id
            FROM reservas JOIN users ON reservas.user_id = users.id
            WHERE reservas.viaje_id IN (SELECT id FROM viajes WHERE user_id = %s)
        """, (session["user_id"],))
        pasajeros = cursor.fetchall()
        cursor.execute("""
            SELECT r.estrellas, r.comentario, r.created_at,
                   u.nombre AS autor_nombre, u.apellido AS autor_apellido
            FROM resenas r JOIN users u ON r.autor_id = u.id
            WHERE r.receptor_id = %s ORDER BY r.created_at DESC
        """, (session["user_id"],))
        resenas_recibidas = cursor.fetchall()
        # Reseñas ya enviadas por el usuario actual
        cursor.execute("SELECT viaje_id, receptor_id FROM resenas WHERE autor_id = %s", (session["user_id"],))
        resenas_enviadas = {(r["viaje_id"], r["receptor_id"]) for r in cursor.fetchall()}
        promedio = None
        if resenas_recibidas:
            promedio = round(sum(r["estrellas"] for r in resenas_recibidas) / len(resenas_recibidas), 1)
        return render_template("perfil.html",
                               user=user, mis_reservas=mis_reservas,
                               viajes=mis_publicaciones, reservas=pasajeros,
                               cantidad_viajes=len(mis_publicaciones),
                               resenas=resenas_recibidas, promedio=promedio,
                               resenas_enviadas=resenas_enviadas, es_propio=True)
    finally:
        cursor.close()
        conn.close()

@app.route("/editar_perfil", methods=["GET", "POST"])
def editar_perfil():
    if "user_id" not in session:
        return redirect("/login")
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    if request.method == "POST":
        nombre         = request.form.get("nombre", "").strip()
        apellido       = request.form.get("apellido", "").strip()
        nueva_password = request.form.get("nueva_password", "").strip()
        avatar_file    = request.files.get("avatar")
        try:
            avatar_data = None
            if avatar_file and avatar_file.filename:
                file_bytes = avatar_file.read()
                if len(file_bytes) > 2 * 1024 * 1024:
                    flash("La imagen no puede superar los 2MB.")
                    return redirect("/editar_perfil")
                ext = avatar_file.filename.rsplit(".", 1)[-1].lower()
                if ext not in {"jpg", "jpeg", "png", "gif", "webp"}:
                    flash("Formato de imagen no permitido.")
                    return redirect("/editar_perfil")
                b64 = base64.b64encode(file_bytes).decode("utf-8")
                avatar_data = f"data:image/{ext};base64,{b64}"
            if nueva_password:
                if len(nueva_password) < 6:
                    flash("La contraseña debe tener al menos 6 caracteres.")
                    return redirect("/editar_perfil")
                hashed = generate_password_hash(nueva_password)
                if avatar_data:
                    cursor.execute("UPDATE users SET nombre=%s, apellido=%s, password=%s, avatar_data=%s WHERE id=%s",
                                   (nombre, apellido, hashed, avatar_data, session["user_id"]))
                else:
                    cursor.execute("UPDATE users SET nombre=%s, apellido=%s, password=%s WHERE id=%s",
                                   (nombre, apellido, hashed, session["user_id"]))
            else:
                if avatar_data:
                    cursor.execute("UPDATE users SET nombre=%s, apellido=%s, avatar_data=%s WHERE id=%s",
                                   (nombre, apellido, avatar_data, session["user_id"]))
                else:
                    cursor.execute("UPDATE users SET nombre=%s, apellido=%s WHERE id=%s",
                                   (nombre, apellido, session["user_id"]))
            conn.commit()
            session["user_nombre"] = nombre
            flash("¡Perfil actualizado con éxito!")
            return redirect("/perfil")
        except Exception as e:
            conn.rollback()
            print(f"Error editando perfil: {e}")
            flash("Hubo un error al actualizar tu perfil.")
            return redirect("/editar_perfil")
        finally:
            cursor.close()
            conn.close()
    else:
        try:
            cursor.execute("SELECT nombre, apellido, email, telefono, avatar_data FROM users WHERE id = %s", (session["user_id"],))
            user = cursor.fetchone()
            return render_template("editar_perfil.html", user=user)
        finally:
            cursor.close()
            conn.close()

@app.route("/usuario/<int:user_id>")
def perfil_publico(user_id):
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, nombre, apellido, avatar_data FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            flash("Usuario no encontrado.")
            return redirect("/viajes")
        cursor.execute("SELECT * FROM viajes WHERE user_id = %s ORDER BY fecha DESC", (user_id,))
        viajes_usuario = cursor.fetchall()
        cursor.execute("""
            SELECT r.estrellas, r.comentario, r.created_at,
                   u.nombre AS autor_nombre, u.apellido AS autor_apellido
            FROM resenas r JOIN users u ON r.autor_id = u.id
            WHERE r.receptor_id = %s ORDER BY r.created_at DESC
        """, (user_id,))
        resenas = cursor.fetchall()
        promedio = None
        if resenas:
            promedio = round(sum(r["estrellas"] for r in resenas) / len(resenas), 1)
        return render_template("perfil_publico.html",
                               user=user, viajes=viajes_usuario,
                               resenas=resenas, promedio=promedio)
    finally:
        cursor.close()
        conn.close()

@app.route("/crear_viaje", methods=["GET", "POST"])
def crear_viaje():
    if "user_id" not in session:
        return redirect("/login")
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT verificado FROM users WHERE id = %s", (session["user_id"],))
    user_status = cursor.fetchone()
    conn.close()
    if not user_status or not user_status["verificado"]:
        flash("Debés verificar tu cuenta antes de publicar un viaje.")
        return redirect("/verificar")
    fecha_hoy = date.today().isoformat()
    if request.method == "POST":
        origen    = request.form["origen"]
        destino   = request.form["destino"]
        encuentro = request.form["encuentro"]
        fecha     = request.form["fecha"]
        hora      = request.form["hora"]
        lugares   = request.form["lugares"]
        precio    = request.form["precio"]
        conn   = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                INSERT INTO viajes (user_id, origen, destino, encuentro, fecha, hora, lugares, precio, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')
            """, (session["user_id"], origen, destino, encuentro, fecha, hora, lugares, precio))
            conn.commit()
            return redirect("/perfil")
        finally:
            cursor.close()
            conn.close()
    return render_template("crear_viaje.html", fecha_hoy=fecha_hoy)

@app.route("/viajes")
def viajes():
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT viajes.*, users.nombre, users.apellido, users.telefono, users.avatar_data,
                   users.id AS conductor_id,
                   COALESCE(ROUND(AVG(r.estrellas)::numeric, 1), 0) AS promedio_conductor,
                   COUNT(r.id) AS total_resenas
            FROM viajes JOIN users ON viajes.user_id = users.id
            LEFT JOIN resenas r ON r.receptor_id = users.id
            WHERE viajes.lugares > 0 AND viajes.estado = 'pendiente'
              AND (viajes.fecha + viajes.hora)::timestamp > NOW()
            GROUP BY viajes.id, users.nombre, users.apellido, users.telefono, users.avatar_data, users.id
            ORDER BY viajes.fecha, viajes.hora
        """)
        viajes_lista = cursor.fetchall()
        return render_template("viajes.html", viajes=viajes_lista)
    finally:
        cursor.close()
        conn.close()

@app.route("/buscar")
def buscar():
    origen  = request.args.get("origen", "")
    destino = request.args.get("destino", "")
    fecha   = request.args.get("fecha", "")
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            SELECT viajes.*, users.nombre, users.apellido, users.telefono, users.avatar_data,
                   users.id AS conductor_id,
                   COALESCE(ROUND(AVG(r.estrellas)::numeric, 1), 0) AS promedio_conductor,
                   COUNT(r.id) AS total_resenas
            FROM viajes JOIN users ON viajes.user_id = users.id
            LEFT JOIN resenas r ON r.receptor_id = users.id
            WHERE viajes.estado = 'pendiente'
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
        query += """ AND viajes.lugares > 0
                     GROUP BY viajes.id, users.nombre, users.apellido, users.telefono, users.avatar_data, users.id
                     ORDER BY viajes.fecha ASC"""
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        return render_template("viajes.html", viajes=resultados, busqueda=True)
    finally:
        cursor.close()
        conn.close()

@app.route("/reservar/<int:viaje_id>", methods=["POST"])
def reservar(viaje_id):
    if "user_id" not in session:
        return redirect("/login")
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id FROM reservas WHERE viaje_id = %s AND user_id = %s", (viaje_id, session["user_id"]))
        if cursor.fetchone():
            flash("Ya tenés una reserva en este viaje.")
            return redirect("/viajes")
        cursor.execute("""
            SELECT v.*, u.email AS conductor_email, u.nombre AS conductor_nombre
            FROM viajes v JOIN users u ON v.user_id = u.id WHERE v.id = %s
        """, (viaje_id,))
        viaje = cursor.fetchone()
        if viaje and viaje["user_id"] != session["user_id"] and viaje["lugares"] > 0 and viaje["estado"] == "pendiente":
            cursor.execute("INSERT INTO reservas (viaje_id, user_id) VALUES (%s, %s)", (viaje_id, session["user_id"]))
            cursor.execute("UPDATE viajes SET lugares = lugares - 1 WHERE id = %s AND lugares > 0", (viaje_id,))
            conn.commit()
            enviar_aviso(session["user_email"], "Reserva Confirmada",
                         f"<h2>✅ Reserva confirmada</h2><p>Tu viaje {viaje['origen']} → {viaje['destino']} del {viaje['fecha']} está reservado.</p>")
            enviar_aviso(viaje["conductor_email"], "Nuevo Pasajero",
                         f"<h2>🚗 Nuevo pasajero</h2><p>{session.get('user_nombre')} reservó un lugar en tu viaje {viaje['origen']} → {viaje['destino']}.</p>")
            flash("¡Viaje reservado exitosamente!")
        elif viaje and viaje["user_id"] == session["user_id"]:
            flash("No podés reservar tu propio viaje.")
        else:
            flash("No se pudo reservar el viaje.")
    except Exception as e:
        conn.rollback()
        print(f"Error reservando: {e}")
        flash("No se pudo reservar.")
    finally:
        cursor.close()
        conn.close()
    return redirect("/viajes")

@app.route("/viaje/<int:viaje_id>/estado", methods=["POST"])
def cambiar_estado(viaje_id):
    if "user_id" not in session:
        return redirect("/login")
    nuevo_estado = request.form.get("estado")
    if nuevo_estado not in ["pendiente", "en_viaje", "finalizado"]:
        flash("Estado no válido.")
        return redirect("/perfil")
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT user_id FROM viajes WHERE id = %s", (viaje_id,))
        viaje = cursor.fetchone()
        if not viaje or viaje["user_id"] != session["user_id"]:
            flash("No tenés permiso para modificar este viaje.")
            return redirect("/perfil")
        cursor.execute("UPDATE viajes SET estado = %s WHERE id = %s", (nuevo_estado, viaje_id))
        conn.commit()
        flash("Estado del viaje actualizado.")
    finally:
        cursor.close()
        conn.close()
    return redirect("/perfil")

@app.route("/cancelar_viaje/<int:viaje_id>", methods=["POST"])
def cancelar_viaje(viaje_id):
    if "user_id" not in session:
        return redirect("/login")
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT user_id FROM viajes WHERE id = %s", (viaje_id,))
        viaje = cursor.fetchone()
        if not viaje or viaje["user_id"] != session["user_id"]:
            flash("No tenés permiso para cancelar este viaje.")
            return redirect("/perfil")
        cursor.execute("SELECT u.email FROM reservas r JOIN users u ON r.user_id = u.id WHERE r.viaje_id = %s", (viaje_id,))
        pasajeros = cursor.fetchall()
        cursor.execute("DELETE FROM reservas WHERE viaje_id = %s", (viaje_id,))
        cursor.execute("DELETE FROM viajes WHERE id = %s", (viaje_id,))
        conn.commit()
        for p in pasajeros:
            enviar_aviso(p["email"], "Viaje Cancelado", "El conductor canceló el viaje.")
    finally:
        cursor.close()
        conn.close()
    return redirect("/perfil")

@app.route("/cancelar_reserva/<int:reserva_id>", methods=["POST"])
def cancelar_reserva(reserva_id):
    if "user_id" not in session:
        return redirect("/login")
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT r.viaje_id, r.user_id, u.email AS conductor_email
            FROM reservas r JOIN viajes v ON r.viaje_id = v.id JOIN users u ON v.user_id = u.id
            WHERE r.id = %s
        """, (reserva_id,))
        datos = cursor.fetchone()
        if datos and datos["user_id"] == session["user_id"]:
            cursor.execute("DELETE FROM reservas WHERE id = %s", (reserva_id,))
            cursor.execute("UPDATE viajes SET lugares = lugares + 1 WHERE id = %s", (datos["viaje_id"],))
            conn.commit()
            enviar_aviso(datos["conductor_email"], "Lugar liberado", "Un pasajero canceló su lugar en tu viaje.")
            flash("Reserva cancelada.")
        else:
            flash("No podés cancelar esta reserva.")
    finally:
        cursor.close()
        conn.close()
    return redirect("/perfil")

@app.route("/resena/<int:viaje_id>/<int:receptor_id>", methods=["POST"])
def dejar_resena(viaje_id, receptor_id):
    if "user_id" not in session:
        return redirect("/login")
    estrellas  = int(request.form.get("estrellas", 0))
    comentario = request.form.get("comentario", "").strip()[:500]
    if not (1 <= estrellas <= 5):
        flash("Calificación inválida.")
        return redirect("/perfil")
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Verificar que el viaje está finalizado
        cursor.execute("SELECT id, user_id FROM viajes WHERE id = %s AND estado = 'finalizado'", (viaje_id,))
        viaje = cursor.fetchone()
        if not viaje:
            flash("Solo podés calificar viajes finalizados.")
            return redirect("/perfil")

        # Verificar que el autor participó (como conductor O como pasajero)
        es_conductor = viaje["user_id"] == session["user_id"]
        cursor.execute("SELECT id FROM reservas WHERE viaje_id = %s AND user_id = %s",
                       (viaje_id, session["user_id"]))
        es_pasajero = cursor.fetchone() is not None

        if not es_conductor and not es_pasajero:
            flash("Solo podés calificar viajes en los que participaste.")
            return redirect("/perfil")

        # Verificar que no se califica a sí mismo
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
        conn.rollback()
        print(f"Error en reseña: {e}")
        flash("No se pudo enviar la reseña.")
    finally:
        cursor.close()
        conn.close()
    return redirect("/perfil")


def enviar_aviso(email_destino, asunto, mensaje):
    api_key = os.environ.get("RESEND_API_KEY")
    url     = "https://api.resend.com/emails"
    html_template = f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
        <div style="background:#E76F51;color:white;padding:15px;"><h1>Ruta Compartida</h1></div>
        <div style="padding:20px;">{mensaje}</div>
        <div style="background:#f2f2f2;padding:10px;text-align:center;"><small>© 2026 Ruta Compartida</small></div></div>"""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"from": "Ruta Compartida <avisos@rutacompartida.com.ar>",
            "to": email_destino, "subject": asunto, "html": html_template}
    try:
        requests.post(url, headers=headers, json=data, timeout=10)
    except Exception as e:
        print(f"Error enviando aviso: {e}")

@app.route("/terminos")
def terminos():
    return render_template("terminos.html")

@app.route("/viajes/<int:viaje_id>")
def ver_viaje(viaje_id):
    conn   = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT viajes.*, users.nombre, users.apellido, users.telefono,
                   users.id AS conductor_id, users.avatar_data,
                   COALESCE(ROUND(AVG(r.estrellas)::numeric,1), 0) AS promedio_conductor,
                   COUNT(r.id) AS total_resenas
            FROM viajes JOIN users ON viajes.user_id = users.id
            LEFT JOIN resenas r ON r.receptor_id = users.id
            WHERE viajes.id = %s
            GROUP BY viajes.id, users.nombre, users.apellido, users.telefono, users.id, users.avatar_data
        """, (viaje_id,))
        viaje = cursor.fetchone()
        if not viaje:
            return redirect("/viajes")
        return render_template("ver_viaje.html", viaje=viaje)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migrations()
    app.run(debug=True)
