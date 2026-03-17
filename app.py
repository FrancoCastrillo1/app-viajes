from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import date
from email.message import EmailMessage
import smtplib
#import resend
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
        
        codigo = str(random.randint(100000, 999999))

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Guardamos el usuario con el código
            cursor.execute("""
                INSERT INTO users (nombre, apellido, telefono, email, password, codigo_verificacion, verificado)
                VALUES (%s, %s, %s, %s, %s, %s, FALSE)
                RETURNING id
            """, (nombre, apellido, telefono, email, password, codigo))
            
            new_user = cursor.fetchone()
            conn.commit()

            # Mandamos el mail usando la nueva función de Gmail
            if enviar_mail_verificacion(email, codigo):
                session["user_id"] = new_user["id"]
                return redirect("/verificar")
            else:
                flash("Error al enviar el mail. Por favor intenta más tarde.")
                return redirect("/register")
                
        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")

#ENVIAR MAIL
def enviar_mail_verificacion(email_destino, codigo):
    email_emisor = os.environ.get("GMAIL_USER")
    password_emisor = os.environ.get("GMAIL_PASS")

    msg = EmailMessage()
    msg.set_content(f"¡Hola! Tu código de verificación es: {codigo}")
    msg["Subject"] = "Código de Verificación - Franco-Viajes"
    msg["From"] = f"Franco-Viajes <{email_emisor}>"
    msg["To"] = email_destino

    try:
        # CAMBIO AQUÍ: Usamos SMTP normal y luego activamos TLS
        # Puerto 587 en lugar de 465
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as smtp: 
            smtp.starttls() # Esto activa la seguridad
            smtp.login(email_emisor, password_emisor)
            smtp.send_message(msg)
        print("¡MAIL ENVIADO CON ÉXITO!")
        return True
    except Exception as e:
        print(f"ERROR AL ENVIAR MAIL: {e}")
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

        # Reservas que hizo el usuario
        cursor.execute("""
            SELECT viajes.*, conductor.nombre AS conductor_nombre, conductor.apellido AS conductor_apellido
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

if __name__ == "__main__":
    app.run(debug=True)
