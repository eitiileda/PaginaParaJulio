"""Factory de la aplicación GameMarket."""
from flask import Flask
from config import Config
from .extensions import db


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )
    app.config.from_object(config_class)
    db.init_app(app)

    from . import models  # Registra los modelos en SQLAlchemy.
    from .routes import registrar_rutas
    registrar_rutas(app)

    # Base local vacía para que el proyecto pueda arrancar sin configurar MySQL.
    # En producción, usar migraciones en lugar de create_all().
    with app.app_context():
        db.create_all()

    return app
