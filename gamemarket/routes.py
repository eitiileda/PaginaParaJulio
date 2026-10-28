"""Rutas web. Cada página queda separada para poder añadir módulos gradualmente."""
from decimal import Decimal, InvalidOperation

from flask import render_template, request, redirect, url_for, current_app
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db
from .models import Usuario, Producto, Publicacion


PAGINAS = {
    "busqueda.html": "busqueda.html",
    "categorias.html": "categorias.html",
    "tal_categoria.html": "tal_categoria.html",
    "producto.html": "producto.html",
    "carrito.html": "carrito.html",
    "historial.html": "historial.html",
    "mas_opciones.html": "mas_opciones.html",
    "ofertas.html": "ofertas.html",
    "publicacion.html": "publicacion.html",
    "chats.html": "chats.html",
}


def registrar_rutas(app):
    @app.get("/")
    @app.get("/index.html")
    def index():
        # El inicio todavía es una maqueta. Si hay datos, quedan disponibles para la plantilla.
        try:
            publicaciones = (
                Publicacion.query.filter_by(estado="activo")
                .order_by(Publicacion.fecha.desc())
                .limit(12)
                .all()
            )
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.info("No se pudieron cargar publicaciones; mostrando la maqueta.")
            publicaciones = []
        return render_template("index.html", publicaciones=publicaciones)

    @app.get("/publicacion/<int:id_publicacion>")
    def detalle_publicacion(id_publicacion):
        publicacion = Publicacion.query.get_or_404(id_publicacion)
        return render_template("detalle.html", publicacion=publicacion)

    @app.route("/upload.html", methods=["GET", "POST"])
    def upload():
        error = None
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            descripcion = request.form.get("descripcion", "").strip()
            logo = request.form.get("logo", "").strip() or None
            descripcion_vendedor = request.form.get("descripcion_vendedor", "").strip()
            id_usuario_raw = request.form.get("id_usuario", "").strip()
            stock_raw = request.form.get("stock", "1").strip()
            precio_raw = request.form.get("precio", "").strip()

            try:
                id_usuario = int(id_usuario_raw)
                stock = int(stock_raw)
                precio = Decimal(precio_raw)
                if not nombre or stock < 0 or precio <= 0 or not precio.is_finite():
                    raise ValueError
                if precio > Decimal("99999999.99"):
                    raise ValueError
            except (ValueError, InvalidOperation):
                error = "Revisá el nombre, vendedor, stock y precio. El precio debe ser mayor a cero."
            else:
                try:
                    vendedor = db.session.get(Usuario, id_usuario)
                    if vendedor is None:
                        raise ValueError("El vendedor seleccionado no existe.")
                    producto = Producto(nombre=nombre, descripcion=descripcion, logo=logo)
                    db.session.add(producto)
                    db.session.flush()
                    publicacion = Publicacion(
                        producto=producto,
                        vendedor=vendedor,
                        stock=stock,
                        precio=precio,
                        descripcion_vendedor=descripcion_vendedor,
                    )
                    db.session.add(publicacion)
                    db.session.commit()
                    return redirect(url_for("index"))
                except ValueError as exc:
                    db.session.rollback()
                    error = str(exc)
                except SQLAlchemyError:
                    db.session.rollback()
                    current_app.logger.exception("Error al guardar una publicación.")
                    error = "No se pudo guardar el producto. Revisá la conexión y la base de datos."

        try:
            vendedores = Usuario.query.filter_by(vendedor=True).order_by(Usuario.nombre).all()
        except SQLAlchemyError:
            db.session.rollback()
            vendedores = []
            error = error or "No se pudo conectar con la base de datos. Revisá la configuración."
        return render_template("upload.html", vendedores=vendedores, error=error)

    @app.get("/detalle.html")
    def detalle_demo():
        id_publicacion = request.args.get("id", type=int)
        if id_publicacion:
            publicacion = db.session.get(Publicacion, id_publicacion)
            if publicacion:
                return render_template("detalle.html", publicacion=publicacion)
        return redirect(url_for("index"))

    for ruta, plantilla in PAGINAS.items():
        endpoint = ruta.removesuffix(".html").replace("-", "_")
        app.add_url_rule(
            "/" + ruta,
            endpoint=endpoint,
            view_func=lambda plantilla=plantilla: render_template(plantilla),
            methods=["GET"],
        )
