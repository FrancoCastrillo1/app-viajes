

from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import date
from email.message import EmailMessage
#import smtplib
#import resend
import requests
import random

#resend.api_key = "re_39rnQkqH_NBoNsYkeoferdxo2Lv4dGrKL"

app = Flask(__name__)
app.secret_key = "clave_secreta"

#resend.api_key = os.environ.get("RESEND_API_KEY")

# FUNCIÓN DE CONEXIÓN (La clave para que no falle)
def get_db_connection():
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        sslmode="require"
    )

# HOME
@app.route("/")
def index():
    return render_template("index.html")

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        telefono = request.form["telefono"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        
        # Generamos el código de 6 dígitos
        codigo = str(random.randint(100000, 999999))

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # 1. Intentamos insertar en la base de datos
            cursor.execute("""
                INSERT INTO users (nombre, apellido, telefono, email, password, codigo_verificacion, verificado)
                VALUES (%s, %s, %s, %s, %s, %s, FALSE)
                RETURNING id
            """, (nombre, apellido, telefono, email, password, codigo))
            
            new_user = cursor.fetchone()
            conn.commit()

            # 2. Intentamos mandar el mail (Si falla, solo sale un print en el log)
            # No usamos "if" aquí para que no trabe la navegación
            enviar_mail_verificacion(email, codigo)

            # 3. Guardamos sesión y REDIRIGIMOS SÍ O SÍ
            session["user_id"] = new_user["id"]
            return redirect("/verificar")

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("Este email ya está registrado. Por favor, inicia sesión.")
            return redirect("/register")
        except Exception as e:
            conn.rollback()
            print(f"Error inesperado en registro: {e}")
            flash("Hubo un error al procesar tu registro.")
            return redirect("/register")
        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")

#ENVIAR MAIL
def enviar_mail_verificacion(email_destino, codigo):
    api_key = os.environ.get("RESEND_API_KEY")
    
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # CAMBIO CLAVE AQUÍ: Usamos tu dominio verificado
    data = {
        "from": "Ruta Compartida <verificacion@rutacompartida.com.ar>",
        "to": email_destino,
        "subject": "Tu código de verificación - Ruta Compartida",
        "html": f"""
        <div style="font-family: sans-serif; text-align: center; border: 2px solid #E76F51; padding: 20px; border-radius: 15px; max-width: 400px; margin: auto;">
            <h2 style="color: #E76F51; margin-bottom: 10px;">¡Hola! 👋</h2>
            <p style="font-size: 1.1rem; color: #333;">Tu código de seguridad para activar tu cuenta en <strong>Ruta Compartida</strong> es:</p>
            <div style="background-color: #FFEDD5; color: #E76F51; padding: 15px; font-size: 2rem; font-weight: bold; border-radius: 10px; margin: 20px 0; letter-spacing: 5px;">
                {codigo}
            </div>
            <p style="color: #666; font-size: 0.9rem;">Si no solicitaste este código, podés ignorar este mensaje.</p>
            <hr style="border: 0.5px solid #eee; margin: 20px 0;">
            <p style="font-size: 0.8rem; color: #999;">© 2026 Ruta Compartida - Viajes Seguros</p>
        </div>
        """
    }

    try:
        # Aumentamos un poquito el timeout por si la API de Resend tarda en responder desde Brasil
        response = requests.post(url, headers=headers, json=data, timeout=15)
        if response.status_code in [200, 201]:
            print(f"¡API RESEND: Mail enviado con éxito a {email_destino}!")
            return True
        else:
            print(f"Error API Resend: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error de conexión con Resend: {e}")
        return False



#VERIFICAR EMAIL

@app.route("/verificar", methods=["GET", "POST"])
def verificar():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        codigo_ingresado = request.form["codigo"]

        conn = get_db_connection()
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
                flash("Código incorrecto.")
        finally:
            cursor.close()
            conn.close()

    return render_template("verificar.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            # ESTAS DOS LÍNEAS SON LAS QUE TE FALTAN:
            session["user_email"] = user["email"] 
            session["user_nombre"] = user["nombre"]
            
            flash("¡Bienvenido de nuevo!")
            return redirect("/viajes")
        else:
            flash("Email o contraseña incorrectos")
    
    return render_template("login.html")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# CREAR VIAJE
@app.route("/crear_viaje", methods=["GET", "POST"])
def crear_viaje():
    if "user_id" not in session:
        return redirect("/login")
    
    # Dentro de @app.route("/crear_viaje")
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT verificado FROM users WHERE id = %s", (session["user_id"],))
    user_status = cursor.fetchone()
    conn.close()

    if not user_status or not user_status['verificado']:
        flash("Debes verificar tu cuenta antes de publicar un viaje.")
        return redirect("/verificar")

    
    fecha_hoy = date.today().isoformat()
    if request.method == "POST":
        origen = request.form["origen"]
        destino = request.form["destino"]
        encuentro = request.form["encuentro"]
        fecha = request.form["fecha"]
        hora = request.form["hora"]
        lugares = request.form["lugares"]
        precio = request.form["precio"]

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                INSERT INTO viajes (user_id, origen, destino, encuentro, fecha, hora, lugares, precio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (session["user_id"], origen, destino, encuentro, fecha, hora, lugares, precio))
            conn.commit()
            return redirect("/viajes")
        finally:
            cursor.close()
            conn.close()

    return render_template("crear_viaje.html", fecha_hoy=fecha_hoy)

# VER VIAJES
@app.route("/viajes")
def viajes():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Nota: Usamos ::timestamp para comparar fecha y hora correctamente en Postgres
        cursor.execute("""
            SELECT viajes.*, users.nombre, users.apellido, users.telefono
            FROM viajes
            JOIN users ON viajes.user_id = users.id
            WHERE viajes.lugares > 0
            AND (viajes.fecha + viajes.hora)::timestamp > NOW()
            ORDER BY viajes.fecha, viajes.hora
        """)
        viajes_lista = cursor.fetchall()
        return render_template("viajes.html", viajes=viajes_lista)
    finally:
        cursor.close()
        conn.close()

# RESERVAR
@app.route("/reservar/<int:viaje_id>", methods=["POST"])
def reservar(viaje_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # CORRECCIÓN AQUÍ: Agregamos u.nombre
        cursor.execute("""
            SELECT v.*, u.email as conductor_email, u.nombre as conductor_nombre 
            FROM viajes v 
            JOIN users u ON v.user_id = u.id 
            WHERE v.id = %s
        """, (viaje_id,))
        viaje = cursor.fetchone()

        if viaje and viaje["user_id"] != session["user_id"]:
            # Tu lógica de insertar y descontar se mantiene igual
            cursor.execute("INSERT INTO reservas (viaje_id, user_id) VALUES (%s, %s)", (viaje_id, session["user_id"]))
            cursor.execute("UPDATE viajes SET lugares = lugares - 1 WHERE id = %s AND lugares > 0", (viaje_id,))
            conn.commit()
            
            # Ahora sí, viaje['conductor_nombre'] va a tener datos
            mensaje_usuario = f"""
            <h2>✅ Reserva confirmada</h2>
            <p>Hola {session.get("user_nombre", "viajero")},</p>
            <p>Tu lugar ya está reservado 🎉</p>

            <h3>📍 Detalles del viaje</h3>
            <ul>
                <li><strong>Ruta:</strong> {viaje['origen']} → {viaje['destino']}</li>
                <li><strong>Fecha:</strong> {viaje['fecha']}</li>
                <li><strong>Hora:</strong> {viaje['hora']}</li>
            </ul>
            
            <h3>👤 Conductor</h3>
            <p>{viaje['conductor_nombre']}</p>
            <p>⚠️ Te recomendamos llegar 5-10 minutos antes.</p>
            <p>Gracias por usar <strong>Ruta Compartida</strong> 🚗</p>
            """
            
            mensaje_conductor = f"""
            <h2>🚗 Tenés un nuevo pasajero</h2>
            <p>Hola {viaje['conductor_nombre']},</p>
            <p>Alguien reservó un lugar en tu viaje 👇</p>

            <h3>📍 Detalles del viaje</h3>
            <ul>
                <li><strong>Ruta:</strong> {viaje['origen']} → {viaje['destino']}</li>
                <li><strong>Fecha:</strong> {viaje['fecha']}</li>
                <li><strong>Hora:</strong> {viaje['hora']}</li>
            </ul>

            <h3>👤 Pasajero</h3>
            <p>{session.get("user_nombre", "Usuario")}</p>
            <p>📲 Te recomendamos contactarte para coordinar el punto de encuentro.</p>
            <p>Equipo de Ruta Compartida</p>
            """
            
            # ENVIAR MAILS
            enviar_aviso(session["user_email"], "Reserva Confirmada", mensaje_usuario)
            enviar_aviso(viaje["conductor_email"], "Nuevo Pasajero", mensaje_conductor)

            flash("¡Viaje reservado exitosamente!")
    except Exception as e:
        print(f"Error: {e}")
        flash("No se pudo reservar.")
    finally:
        cursor.close()
        conn.close()
    return redirect("/viajes")

# PERFIL
@app.route("/perfil")
def perfil():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Datos del usuario
        cursor.execute("SELECT nombre, apellido, telefono, email FROM users WHERE id = %s", (session["user_id"],))
        user = cursor.fetchone()

        # --- MODIFICADO: Reservas que hizo el usuario (incluimos ID de reserva y Teléfono) ---
        cursor.execute("""
            SELECT 
                viajes.*, 
                reservas.id AS reserva_id,
                conductor.nombre AS conductor_nombre, 
                conductor.apellido AS conductor_apellido,
                conductor.telefono AS conductor_telefono
            FROM reservas
            JOIN viajes ON reservas.viaje_id = viajes.id
            JOIN users AS conductor ON viajes.user_id = conductor.id
            WHERE reservas.user_id = %s
        """, (session["user_id"],))
        mis_reservas = cursor.fetchall()

        # Viajes que publicó el usuario
        cursor.execute("SELECT * FROM viajes WHERE user_id = %s ORDER BY fecha DESC", (session["user_id"],))
        mis_publicaciones = cursor.fetchall()

        # Quién reservó mis viajes (para ver los pasajeros)
        cursor.execute("""
            SELECT reservas.viaje_id, users.nombre, users.apellido
            FROM reservas
            JOIN users ON reservas.user_id = users.id
        """)
        pasajeros = cursor.fetchall()

        return render_template("perfil.html", 
                               user=user, 
                               mis_reservas=mis_reservas, 
                               viajes=mis_publicaciones, 
                               reservas=pasajeros, 
                               cantidad_viajes=len(mis_publicaciones))
    finally:
        cursor.close()
        conn.close()
        
#CANCELAR VIAJE
     
@app.route("/cancelar_viaje/<int:viaje_id>", methods=["POST"])
@app.route("/cancelar_viaje/<int:viaje_id>", methods=["POST"])
def cancelar_viaje(viaje_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # 1. Buscar pasajeros antes de borrar
        cursor.execute("SELECT u.email FROM reservas r JOIN users u ON r.user_id = u.id WHERE r.viaje_id = %s", (viaje_id,))
        pasajeros = cursor.fetchall()

        # 2. Borrar (Tu código original)
        cursor.execute("DELETE FROM reservas WHERE viaje_id = %s", (viaje_id,))
        cursor.execute("DELETE FROM viajes WHERE id = %s", (viaje_id,))
        conn.commit()

        # 3. Avisar a todos
        for p in pasajeros:
            enviar_aviso(p['email'], "Viaje Cancelado", "El conductor canceló el viaje.")

    finally:
        cursor.close()
        conn.close()
    return redirect("/perfil")

#CANCELAR RESERVA
@app.route("/cancelar_reserva/<int:reserva_id>", methods=["POST"])
def cancelar_reserva(reserva_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Buscamos al conductor antes de borrar la reserva
        cursor.execute("""
            SELECT v.id as viaje_id, u.email as conductor_email 
            FROM reservas r
            JOIN viajes v ON r.viaje_id = v.id
            JOIN users u ON v.user_id = u.id
            WHERE r.id = %s
        """, (reserva_id,))
        datos = cursor.fetchone()

        if datos:
            # Tu lógica original de borrar y sumar lugar
            cursor.execute("DELETE FROM reservas WHERE id = %s", (reserva_id,))
            cursor.execute("UPDATE viajes SET lugares = lugares + 1 WHERE id = %s", (datos['viaje_id'],))
            conn.commit()

            # AVISO AL CONDUCTOR
            enviar_aviso(datos['conductor_email'], "Lugar liberado", "Un pasajero canceló su lugar en tu viaje.")
            flash("Reserva cancelada.")
    finally:
        cursor.close()
        conn.close()
    return redirect("/perfil")

#FILTRO DE BUSQUEDA VIAJES

@app.route("/buscar")
def buscar():
    origen = request.args.get("origen", "")
    destino = request.args.get("destino", "")
    fecha = request.args.get("fecha", "")

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            SELECT viajes.*, users.nombre, users.apellido, users.telefono 
            FROM viajes 
            JOIN users ON viajes.user_id = users.id 
            WHERE 1=1
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

        query += " AND viajes.lugares > 0 ORDER BY viajes.fecha ASC"
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        # Reutilizamos viajes.html para mostrar los resultados
        return render_template("viajes.html", viajes=resultados, busqueda=True)
    finally:
        cursor.close()
        conn.close()
        
#ENVIAR NOTIFICACIONES POR EMAIL

def enviar_aviso(email_destino, asunto, mensaje):
    api_key = os.environ.get("RESEND_API_KEY")
    url = "https://api.resend.com/emails"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "from": "Ruta Compartida <avisos@rutacompartida.com.ar>",
        "to": email_destino,
        "subject": asunto,
        "html": f"<p>{mensaje}</p>"
    }
    requests.post(url, headers=headers, json=data)

#IR A TERMINOS Y CONDICIONES
@app.route('/terminos')
def terminos():
    return render_template('terminos.html')

@app.route("/viajes/<int:viaje_id>")
def ver_viaje(viaje_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT viajes.*, users.nombre, users.apellido, users.telefono
            FROM viajes
            JOIN users ON viajes.user_id = users.id
            WHERE viajes.id = %s
        """, (viaje_id,))
        viaje = cursor.fetchone()
        if not viaje:
            return redirect("/viajes")
        return render_template("ver_viaje.html", viaje=viaje)
    finally:
        cursor.close()
        conn.close()



if __name__ == "__main__":
    app.run(debug=True)
