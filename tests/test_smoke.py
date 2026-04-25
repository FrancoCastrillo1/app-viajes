"""
Smoke tests — verifica que las rutas principales responden sin crashear.
Las rutas que consultan la BD usan el fixture mock_db_empty de conftest.
"""


# ── Sin BD ───────────────────────────────────────────────────────────────────

def test_homepage_returns_200(client):
    assert client.get("/").status_code == 200


def test_login_page_returns_200(client):
    assert client.get("/login").status_code == 200


def test_register_page_returns_200(client):
    assert client.get("/register").status_code == 200


def test_terminos_returns_200(client):
    assert client.get("/terminos").status_code == 200


def test_unknown_route_returns_404(client):
    assert client.get("/ruta-que-no-existe-xyz-123").status_code == 404


# ── Rutas protegidas redirigen sin sesión ────────────────────────────────────

def test_perfil_sin_sesion_redirige(client):
    r = client.get("/perfil")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_crear_viaje_sin_sesion_redirige(client):
    r = client.get("/crear_viaje")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_editar_perfil_sin_sesion_redirige(client):
    r = client.get("/editar_perfil")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_verificar_sin_sesion_redirige(client):
    r = client.get("/verificar")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


# ── Con mock de BD ───────────────────────────────────────────────────────────

def test_viajes_returns_200(client, mock_db_empty):
    assert client.get("/viajes").status_code == 200


def test_buscar_returns_200(client, mock_db_empty):
    assert client.get("/buscar?origen=Leones&destino=Rosario").status_code == 200


def test_buscar_sin_params_returns_200(client, mock_db_empty):
    assert client.get("/buscar").status_code == 200


def test_ver_viaje_inexistente_redirige(client, mock_db_empty):
    # fetchone devuelve None → redirige a /viajes
    r = client.get("/viajes/99999")
    assert r.status_code == 302


def test_perfil_publico_inexistente_redirige(client, mock_db_empty):
    # fetchone devuelve None → redirige a /viajes
    r = client.get("/usuario/99999")
    assert r.status_code == 302
