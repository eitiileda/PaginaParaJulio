"""Factory de la aplicación GameMarket."""
from flask import Flask, jsonify, redirect, request, url_for
from config import Config
from .extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )
    app.config.from_object(config_class)
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "iniciar_sesion"
    login_manager.login_message = None

    @login_manager.unauthorized_handler
    def redirigir_a_inicio_de_sesion():
        if request.path.startswith("/api/"):
            return jsonify(error="Iniciá sesión para continuar."), 401
        if request.path == "/carrito/confirmar":
            destino = url_for("carrito")
        else:
            destino = request.full_path if request.query_string else request.path
        return redirect(url_for("iniciar_sesion", next=destino))

    from . import models  # Registra los modelos en SQLAlchemy.

    @login_manager.user_loader
    def cargar_usuario(id_usuario):
        try:
            return db.session.get(models.Usuario, int(id_usuario))
        except (TypeError, ValueError):
            return None

    from .routes import registrar_rutas
    registrar_rutas(app)

    # Base local vacía para que el proyecto pueda arrancar sin configurar MySQL.
    # En producción, usar migraciones en lugar de create_all().
    with app.app_context():
        db.create_all()

    return app
