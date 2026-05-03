import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from flask import current_app
import logging

logger = logging.getLogger(__name__)


@contextmanager
def get_db():
    """
    Context manager que abre una conexión psycopg2 y la cierra al salir.
    Yields (conn, cursor) con RealDictCursor.
    El commit/rollback es responsabilidad del llamador.
    """
    conn   = psycopg2.connect(current_app.config["DATABASE_URL"], sslmode="require")
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield conn, cursor
    finally:
        cursor.close()
        conn.close()


def run_migrations(database_url: str) -> None:
    conn   = psycopg2.connect(database_url, sslmode="require")
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_data TEXT;")
        cursor.execute("ALTER TABLE viajes ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'pendiente';")
        # Fase 2: expiración del código de verificación
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS codigo_expiracion TIMESTAMP;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resenas (
                id          SERIAL PRIMARY KEY,
                viaje_id    INTEGER NOT NULL REFERENCES viajes(id)  ON DELETE CASCADE,
                autor_id    INTEGER NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
                receptor_id INTEGER NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
                estrellas   INTEGER NOT NULL CHECK (estrellas BETWEEN 1 AND 5),
                comentario  TEXT,
                created_at  TIMESTAMP DEFAULT NOW(),
                UNIQUE(viaje_id, autor_id, receptor_id)
            );
        """)
        # Recuperación de contraseña
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_codigo VARCHAR(6);")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_expiracion TIMESTAMP;")
        # Fase 2: prevenir reservas duplicadas a nivel de BD
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'reservas_viaje_user_unique'
                ) THEN
                    ALTER TABLE reservas
                        ADD CONSTRAINT reservas_viaje_user_unique UNIQUE (viaje_id, user_id);
                END IF;
            END $$;
        """)
        conn.commit()
        logger.info("Migraciones ejecutadas correctamente.")
    except Exception as e:
        conn.rollback()
        logger.error("Error en migraciones: %s", e, exc_info=True)
    finally:
        cursor.close()
        conn.close()
