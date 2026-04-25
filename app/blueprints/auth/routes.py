import threading
import secrets
import logging
from datetime import datetime, timedelta, timezone

import psycopg2
from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from app.database import get_db
from app.extensions import limiter
import app.utils.email as email_utils

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per hour", methods=["POST"])
def register():
    if request.method == "POST":
        nombre   = request.form["nombre"].strip()
        apellido = request.form["apellido"].strip()
        telefono = request.form["telefono"].strip()
        email    = request.form["email"].strip().lower()
        password = generate_password_hash(request.form["password"])
        codigo      = str(secrets.randbelow(900000) + 100000)
        expiracion  = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
        try:
            with get_db() as (conn, cursor):
                cursor.execute("""
                    INSERT INTO users
                        (nombre, apellido, telefono, email, password,
                         codigo_verificacion, codigo_expiracion, verificado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE)
                    RETURNING id
                """, (nombre, apellido, telefono, email, password, codigo, expiracion))
                new_user = cursor.fetchone()
                conn.commit()
            threading.Thread(
                target=email_utils.enviar_mail_verificacion,
                args=(email, codigo),
                daemon=True,
            ).start()
            session["user_id"]     = new_user["id"]
            session["user_email"]  = email
            session["user_nombre"] = nombre
            return redirect("/verificar")
        except psycopg2.errors.UniqueViolation:
            flash("Este email ya está registrado. Por favor, iniciá sesión.")
            return redirect("/register")
        except Exception as e:
            logger.error("Error en registro: %s", e, exc_info=True)
            flash("Hubo un error al procesar tu registro.")
            return redirect("/register")
    return render_template("register.html")


@auth_bp.route("/verificar", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def verificar():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        codigo_ingresado = request.form["codigo"]
        with get_db() as (conn, cursor):
            cursor.execute(
                "SELECT codigo_verificacion, codigo_expiracion FROM users WHERE id = %s",
                (session["user_id"],),
            )
            user = cursor.fetchone()
            if user and user["codigo_expiracion"] and \
                    user["codigo_expiracion"] < datetime.now(timezone.utc).replace(tzinfo=None):
                flash("El código expiró. Registrate nuevamente.")
                session.clear()
                return redirect("/register")
            if user and user["codigo_verificacion"] == codigo_ingresado:
                cursor.execute(
                    "UPDATE users SET verificado = TRUE WHERE id = %s",
                    (session["user_id"],),
                )
                conn.commit()
                flash("¡Cuenta verificada con éxito!")
                return redirect("/viajes")
            else:
                flash("Código incorrecto. Intentá de nuevo.")
    return render_template("verificar.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as (conn, cursor):
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"]     = user["id"]
            session["user_email"]  = user["email"]
            session["user_nombre"] = user["nombre"]
            flash("¡Bienvenido de nuevo!")
            return redirect("/viajes")
        else:
            flash("Email o contraseña incorrectos.")
    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")
