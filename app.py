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
    
    # IMPORTANTE: En modo prueba de Resend, el 'to' DEBE SER tu mail de registro
    # Para probar que redirija bien, usá franco.castrillo1@gmail.com
    
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "from": "onboarding@resend.dev",
        "to": email_destino,
        "subject": "Tu código de verificación",
        "html": f"<strong>Tu código es: {codigo}</strong>"
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200 or response.status_code == 201:
            print("¡API RESEND: Mail enviado con éxito!")
            return True
        else:
            print(f"Error API Resend: {response.text}")
            return False
    except Exception as e:
        print(f"Error de conexión: {e}")
        return False



#vERIFICAR EMAIL

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
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                return redirect("/viajes")
            else:
                flash("Email o contraseña incorrectos")
                return render_template("login.html")
        finally:
            cursor.close()
            conn.close()

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
        # Verificar si es el mismo conductor
        cursor.execute("SELECT user_id FROM viajes WHERE id = %s", (viaje_id,))
        viaje = cursor.fetchone()
        if viaje and viaje["user_id"] == session["user_id"]:
            return redirect("/viajes")

        # Verificar reserva existente
        cursor.execute("SELECT * FROM reservas WHERE viaje_id = %s AND user_id = %s", (viaje_id, session["user_id"]))
        if cursor.fetchone():
            return redirect("/viajes")
        
        # Realizar reserva y descontar lugar
        cursor.execute("INSERT INTO reservas (viaje_id, user_id) VALUES (%s, %s)", (viaje_id, session["user_id"]))
        cursor.execute("UPDATE viajes SET lugares = lugares - 1 WHERE id = %s AND lugares > 0", (viaje_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    try:
        # Si todo sale bien:
        flash("¡Viaje reservado exitosamente!")
    except:
        flash("No se pudo reservar el viaje. Intentá de nuevo.")
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
        
        
# CANCELAR VIAJE
@app.route("/cancelar_viaje/<int:viaje_id>", methods=["POST"])
def cancelar_viaje(viaje_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT user_id FROM viajes WHERE id = %s", (viaje_id,))
        viaje = cursor.fetchone()

        if viaje and viaje["user_id"] == session["user_id"]:
            cursor.execute("DELETE FROM reservas WHERE viaje_id = %s", (viaje_id,))
            cursor.execute("DELETE FROM viajes WHERE id = %s", (viaje_id,))
            conn.commit()
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
    cursor = conn.cursor()
    try:
        # Borramos la reserva (solo si pertenece al usuario logueado por seguridad)
        cursor.execute("DELETE FROM reservas WHERE id = %s AND user_id = %s", 
                       (reserva_id, session["user_id"]))
        conn.commit()
        flash("Reserva cancelada con éxito.")
    except Exception as e:
        print(f"Error al cancelar: {e}")
        flash("No se pudo cancelar la reserva.")
    finally:
        conn.close()
    flash("Reserva cancelada correctamente.")
    return redirect("/perfil")

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

if __name__ == "__main__":
    app.run(debug=True)
