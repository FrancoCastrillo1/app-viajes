import os
import pytest
from contextlib import contextmanager
from unittest.mock import MagicMock

# Variables mínimas requeridas antes de importar la app
os.environ.setdefault("SECRET_KEY",    "test-secret-key-fase-0-no-usar-en-prod")
os.environ.setdefault("DATABASE_URL",  "postgresql://test:test@localhost/test")
os.environ.setdefault("RESEND_API_KEY", "test-key")

from app import create_app


@pytest.fixture()
def app():
    return create_app("testing")


@pytest.fixture()
def client(app):
    return app.test_client()


# ── Mock de requests.post ────────────────────────────────────────────────────
# Previene que las funciones de email (que corren en threads daemon)
# hagan llamadas HTTP reales durante los tests.

@pytest.fixture(autouse=True)
def no_http(monkeypatch):
    """Bloquea todas las llamadas requests.post en cualquier test."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    monkeypatch.setattr("requests.post", lambda *a, **kw: mock_resp)


# ── Helpers de mock de BD ────────────────────────────────────────────────────

def make_mock_get_db(fetchone_result=None, fetchall_result=None):
    """
    Devuelve (mock_get_db, conn, cursor).
    mock_get_db es un context manager que yields (conn, cursor).
    """
    conn   = MagicMock()
    cursor = MagicMock()
    cursor.fetchone.return_value  = fetchone_result
    cursor.fetchall.return_value  = fetchall_result or []

    @contextmanager
    def mock_get_db():
        yield conn, cursor

    return mock_get_db, conn, cursor


_BLUEPRINT_PATHS = [
    "app.blueprints.auth.routes.get_db",
    "app.blueprints.viajes.routes.get_db",
    "app.blueprints.usuarios.routes.get_db",
    "app.blueprints.reservas.routes.get_db",
]


def patch_get_db(monkeypatch, mock_fn):
    """
    Parchea get_db en todos los blueprints.
    'from app.database import get_db' crea un binding local en cada módulo,
    por eso hay que parchear donde se usa, no donde se define.
    """
    for path in _BLUEPRINT_PATHS:
        monkeypatch.setattr(path, mock_fn)


@pytest.fixture()
def mock_db_empty(monkeypatch):
    """Mock de BD con resultados vacíos — para smoke tests."""
    mock_get_db, conn, cursor = make_mock_get_db()
    patch_get_db(monkeypatch, mock_get_db)
    return conn, cursor
