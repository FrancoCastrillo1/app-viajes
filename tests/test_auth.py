"""
Tests de autenticación — registro, login, logout, verificación.
"""
import pytest
from contextlib import contextmanager
from unittest.mock import MagicMock
from werkzeug.security import generate_password_hash

import psycopg2

from tests.conftest import make_mock_get_db, patch_get_db


# ── /register ────────────────────────────────────────────────────────────────

def test_register_get_returns_200(client):
    assert client.get("/register").status_code == 200


def test_register_post_crea_usuario_y_redirige(client, monkeypatch):
    mock_get_db, conn, cursor = make_mock_get_db(fetchone_result={"id": 1})
    patch_get_db(monkeypatch, mock_get_db)

    r = client.post("/register", data={
        "nombre":   "Juan",
        "apellido": "García",
        "telefono": "3571123456",
        "email":    "juan@test.com",
        "password": "secreto123",
    })
    assert r.status_code == 302
    assert "/verificar" in r.headers["Location"]


def test_register_post_email_duplicado_flashes_error(client, monkeypatch):
    conn   = MagicMock()
    cursor = MagicMock()
    cursor.execute.side_effect = psycopg2.errors.UniqueViolation("duplicate key")

    @contextmanager
    def mock_get_db():
        yield conn, cursor

    patch_get_db(monkeypatch, mock_get_db)

    r = client.post("/register", data={
        "nombre":   "Juan",
        "apellido": "García",
        "telefono": "3571123456",
        "email":    "duplicado@test.com",
        "password": "secreto123",
    })
    assert r.status_code == 302
    assert "/register" in r.headers["Location"]


# ── /login ───────────────────────────────────────────────────────────────────

def test_login_get_returns_200(client):
    assert client.get("/login").status_code == 200


def test_login_post_credenciales_validas_redirige(client, monkeypatch):
    hashed = generate_password_hash("secreto123")
    mock_get_db, _, _ = make_mock_get_db(fetchone_result={
        "id": 1, "email": "juan@test.com",
        "nombre": "Juan", "password": hashed,
    })
    patch_get_db(monkeypatch, mock_get_db)

    r = client.post("/login", data={"email": "juan@test.com", "password": "secreto123"})
    assert r.status_code == 302
    assert "/viajes" in r.headers["Location"]


def test_login_post_password_incorrecta_vuelve_al_form(client, monkeypatch):
    hashed = generate_password_hash("correcta")
    mock_get_db, _, _ = make_mock_get_db(fetchone_result={
        "id": 1, "email": "juan@test.com",
        "nombre": "Juan", "password": hashed,
    })
    patch_get_db(monkeypatch, mock_get_db)

    r = client.post("/login", data={"email": "juan@test.com", "password": "incorrecta"})
    assert r.status_code == 200   # re-renderiza el form, no redirige


def test_login_post_usuario_no_existe(client, monkeypatch):
    mock_get_db, _, _ = make_mock_get_db(fetchone_result=None)
    patch_get_db(monkeypatch, mock_get_db)

    r = client.post("/login", data={"email": "noexiste@test.com", "password": "x"})
    assert r.status_code == 200


# ── /logout ──────────────────────────────────────────────────────────────────

def test_logout_get_returns_405(client):
    r = client.get("/logout")
    assert r.status_code == 405


def test_logout_post_redirige_a_inicio(client):
    r = client.post("/logout")
    assert r.status_code == 302
    assert "/" in r.headers["Location"]


def test_logout_limpia_sesion(client, monkeypatch):
    hashed = generate_password_hash("pass")
    mock_get_db, _, _ = make_mock_get_db(fetchone_result={
        "id": 7, "email": "u@test.com", "nombre": "U", "password": hashed,
    })
    patch_get_db(monkeypatch, mock_get_db)

    with client:
        client.post("/login", data={"email": "u@test.com", "password": "pass"})
        from flask import session
        assert "user_id" in session

        client.post("/logout")
        assert "user_id" not in session


# ── /verificar ───────────────────────────────────────────────────────────────

def test_verificar_sin_sesion_redirige_a_login(client):
    r = client.get("/verificar")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_verificar_codigo_correcto_redirige_a_viajes(client, monkeypatch):
    mock_get_db, _, _ = make_mock_get_db(
        fetchone_result={"codigo_verificacion": "123456", "codigo_expiracion": None}
    )
    patch_get_db(monkeypatch, mock_get_db)

    with client.session_transaction() as sess:
        sess["user_id"]     = 1
        sess["user_email"]  = "test@test.com"
        sess["user_nombre"] = "Test"

    r = client.post("/verificar", data={"codigo": "123456"})
    assert r.status_code == 302
    assert "/viajes" in r.headers["Location"]


def test_verificar_codigo_incorrecto_vuelve_al_form(client, monkeypatch):
    mock_get_db, _, _ = make_mock_get_db(
        fetchone_result={"codigo_verificacion": "999999", "codigo_expiracion": None}
    )
    patch_get_db(monkeypatch, mock_get_db)

    with client.session_transaction() as sess:
        sess["user_id"]     = 1
        sess["user_email"]  = "test@test.com"
        sess["user_nombre"] = "Test"

    r = client.post("/verificar", data={"codigo": "000000"})
    assert r.status_code == 200   # re-renderiza el form
