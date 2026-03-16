from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash
import psycopg2
from psycopg2.extras import RealDictCursor
import os

from datetime import date

app = Flask(__name__)
app.secret_key = "clave_secreta"

import psycopg2
import os

db = psycopg2.connect(os.environ["DATABASE_URL"])

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


        cursor = db.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("ERROR: Este email ya está registrado. Inicie sesion o utilice otro email")
            return render_template("register.html")
        
        
        cursor.execute("""
        INSERT INTO users (nombre, apellido, telefono, email, password)
        VALUES (%s, %s, %s, %s, %s)
        """, (nombre, apellido, telefono, email, password))
    
        db.commit()

        return redirect("/login")

    return render_template("register.html")


# LOGIN

@app.route("/login", methods=["GET", "POST"])
def login():
    
    
    
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect("/viajes")  

    return render_template("login.html")

#LOG OUT

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



# CREAR VIAJE

@app.route("/crear_viaje", methods=["GET", "POST"])
def crear_viaje():
    fecha_hoy = date.today().isoformat()
    if request.method == "POST":
        origen = request.form["origen"]
        destino = request.form["destino"]
        encuentro = request.form["encuentro"]
        fecha = request.form["fecha"]
        hora = request.form["hora"]
        lugares = request.form["lugares"]
        precio = request.form["precio"]

        cursor = db.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
    INSERT INTO viajes (user_id, origen, destino, encuentro, fecha, hora, lugares, precio)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", (session["user_id"], origen, destino, encuentro, fecha, hora, lugares, precio))

        db.commit()

        return redirect("/viajes")

    return render_template("crear_viaje.html", fecha_hoy=fecha_hoy)


# VER VIAJES

# VER VIAJES

@app.route("/viajes")
def viajes():

    cursor = db.cursor(cursor_factory=RealDictCursor)


    cursor.execute("""
        SELECT viajes.*, users.nombre, users.apellido, users.telefono
        FROM viajes
        JOIN users ON viajes.user_id = users.id
        WHERE viajes.lugares > 0
        AND CONCAT(viajes.fecha, ' ', viajes.hora) > NOW()
        ORDER BY viajes.fecha, viajes.hora
    """)

    viajes = cursor.fetchall()

    return render_template("viajes.html", viajes=viajes)

#RESERVAR

@app.route("/reservar/<int:viaje_id>", methods=["POST"])
def reservar(viaje_id):

    if "user_id" not in session:
        return redirect("/login")

    cursor = db.cursor(cursor_factory=RealDictCursor)


    cursor.execute("""
        SELECT *
        FROM reservas
        WHERE viaje_id = %s AND user_id = %s
    """, (viaje_id, session["user_id"]))
    
    reserva_existente = cursor.fetchone()
    
    if reserva_existente:
        return redirect("/viajes")
    
    cursor.execute("""
        INSERT INTO reservas (viaje_id, user_id)
        VALUES (%s, %s)
    """, (viaje_id, session["user_id"]))

    cursor.execute("""
        UPDATE viajes
        SET lugares = lugares - 1
        WHERE id = %s
    """, (viaje_id,))

    db.commit()

    return redirect("/viajes")

#PERFIL USUARIOS

@app.route("/perfil")
def perfil():

    if "user_id" not in session:
        return redirect("/login")

    cursor = db.cursor(cursor_factory=RealDictCursor)


    # datos del usuario
    cursor.execute("""
        SELECT nombre, apellido, telefono, email
        FROM users
        WHERE id = %s
    """, (session["user_id"],))

    user = cursor.fetchone()

    # reservas del usuario
    cursor.execute("""
    SELECT 
        viajes.origen,
        viajes.destino,
        viajes.fecha,
        viajes.hora,
        viajes.precio,
        conductor.nombre AS conductor_nombre,
        conductor.apellido AS conductor_apellido
    FROM reservas
    JOIN viajes ON reservas.viaje_id = viajes.id
    JOIN users AS conductor ON viajes.user_id = conductor.id
    WHERE reservas.user_id = %s
    """, (session["user_id"],))

    mis_reservas = cursor.fetchall()


    # viajes publicados
    cursor.execute("""
        SELECT *
        FROM viajes
        WHERE user_id = %s
        ORDER BY fecha DESC
    """, (session["user_id"],))

    viajes = cursor.fetchall()

    # cantidad de viajes
    cantidad_viajes = len(viajes)

    # reservas de los viajes
    cursor.execute("""
        SELECT reservas.viaje_id, users.nombre, users.apellido
        FROM reservas
        JOIN users ON reservas.user_id = users.id
    """)

    reservas = cursor.fetchall()

    return render_template(
        "perfil.html",
        user=user,
        viajes=viajes,
        reservas=reservas,
        mis_reservas=mis_reservas,
        cantidad_viajes=cantidad_viajes
    )
    
#CANCELAR VIAJES

@app.route("/cancelar_viaje/<int:viaje_id>", methods=["POST"])
def cancelar_viaje(viaje_id):

    if "user_id" not in session:
        return redirect("/login")

    cursor = db.cursor(cursor_factory=RealDictCursor)


    cursor.execute("""
        SELECT user_id
        FROM viajes
        WHERE id = %s
    """, (viaje_id,))

    viaje = cursor.fetchone()

    if viaje and viaje["user_id"] == session["user_id"]:

        # borrar reservas primero
        cursor.execute("DELETE FROM reservas WHERE viaje_id = %s", (viaje_id,))

        # borrar el viaje
        cursor.execute("DELETE FROM viajes WHERE id = %s", (viaje_id,))

        db.commit()

    return redirect("/perfil")



if __name__ == "__main__":
    app.run(debug=True)
