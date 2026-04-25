import os


class Config:
    SECRET_KEY   = os.environ.get("SECRET_KEY", "dev-fallback-DO-NOT-USE-IN-PROD")
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    FORCE_HTTPS  = True

    # Lista de (value_en_bd, nombre_visible) — value preserva lo almacenado en BD
    CITIES = [
        ("Leones",       "Leones"),
        ("Marcos Juarez","Marcos Juarez"),
        ("Rosario",      "Rosario"),
        ("Cordoba",      "Córdoba"),
        ("Villa Maria",  "Villa María"),
        ("Bell ville",   "Bell Ville"),
    ]


class DevelopmentConfig(Config):
    DEBUG = True
    FORCE_HTTPS = False


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    FORCE_HTTPS  = False
    SECRET_KEY   = "test-secret-key-not-for-prod"
    DATABASE_URL = "postgresql://test:test@localhost/test_rutacompartida"
    RESEND_API_KEY = "test-resend-key"


config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
    "default":     DevelopmentConfig,
}
