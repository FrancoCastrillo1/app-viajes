"""
Punto de entrada para Gunicorn y desarrollo local.
  Producción:   gunicorn wsgi:app
  Desarrollo:   flask --app wsgi run  (o python wsgi.py)
"""
import os
from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "production"))

if __name__ == "__main__":
    dev_app = create_app("development")
    dev_app.run(
        debug=True,
        port=int(os.environ.get("PORT", 5000)),
    )
