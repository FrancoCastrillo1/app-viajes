import os
import sys
import logging
from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app(config_name: str | None = None) -> Flask:
    """
    Application Factory.
    config_name: "development" | "production" | "testing" | None (usa FLASK_ENV o "default")
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )

    from app.config import config as app_config
    app.config.from_object(app_config[config_name])

    if config_name == "production":
        if not os.environ.get("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY debe estar configurado en producción.")
        if not os.environ.get("DATABASE_URL"):
            raise RuntimeError("DATABASE_URL debe estar configurado en producción.")

    _configure_logging(app)

    # Extensions
    from app.extensions import csrf, limiter, talisman
    csrf.init_app(app)
    limiter.init_app(app)
    talisman.init_app(
        app,
        force_https=app.config.get("FORCE_HTTPS", True),
        content_security_policy={
            "default-src": "'self'",
            "script-src":  ["'self'", "'unsafe-inline'"],
            "style-src":   ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            "font-src":    ["'self'", "https://fonts.gstatic.com"],
            "img-src":     ["'self'", "data:"],
        },
    )

    # Blueprints
    from app.blueprints.main.routes     import main_bp
    from app.blueprints.auth.routes     import auth_bp
    from app.blueprints.viajes.routes   import viajes_bp
    from app.blueprints.usuarios.routes import usuarios_bp
    from app.blueprints.reservas.routes import reservas_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(viajes_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(reservas_bp)

    # CLI: flask db-migrate
    @app.cli.command("db-migrate")
    def db_migrate():
        from app.database import run_migrations
        run_migrations(app.config["DATABASE_URL"])
        print("Migraciones completadas.")

    return app


def _configure_logging(app: Flask) -> None:
    if not app.logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

    logging.getLogger("app").setLevel(logging.DEBUG if app.debug else logging.INFO)
