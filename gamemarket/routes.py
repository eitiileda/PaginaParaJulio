"""Rutas web. Cada página queda separada para poder añadir módulos gradualmente."""
import os
import uuid
from decimal import Decimal, InvalidOperation

from flask import (
    render_template, request, redirect, url_for, current_app, jsonify,
)
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db
from .models import Usuario, Producto, Publicacion


# "publicacion.html" ya NO está acá: tiene su propia ruta más abajo,
# porque necesita cargar la lista de vendedores desde la base de datos.
PAGINAS = {
    "busqueda.html": "busqueda.html",
    "categorias.html": "categorias.html",
    "tal_categoria.html": "tal_categoria.html",
    "producto.html": "producto.html",
    "carrito.html": "carrito.html",
    "historial.html": "historial.html",
    "mas_opciones.html": "mas_opciones.html",
    "ofertas.html": "ofertas.html",
    "chats.html": "chats.html",
}

CATEGORIAS = {
    "consolas", "videojuegos", "perifericos", "componentes",
    "pc", "accesorios", "audio",
}
CONDICIONES = {"Nuevo", "Usado", "Reacondicionado"}
PRECIO_MAX = Decimal("99999999.99")  # límite de DECIMAL(10,2)


def _extension_imagen(cabecera: bytes):
    """Devuelve la extensión real según los primeros bytes del archivo.

    No alcanza con mirar el nombre o el Content-Type: los manda el cliente
    y se pueden falsificar.
    """
    if cabecera.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if cabecera.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if cabecera[:4] == b"RIFF" and cabecera[8:12] == b"WEBP":
        return "webp"
    return None


def _error(mensaje, codigo=400):
    return jsonify(error=mensaje), codigo


def registrar_rutas(app):
    @app.errorhandler(413)
    def archivo_muy_grande(_error_413):
        if request.path.startswith("/api/"):
            return _error("La imagen no puede superar los 5 MB.", 413)
        return "Archivo demasiado grande", 413

    @app.get("/")
    @app.get("/index.html")
    def index():
        try:
            publicaciones = (
                Publicacion.query
                .order_by(Publicacion.fecha.desc())
                .limit(12)
                .all()
            )
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("Error al listar publicaciones.")
            publicaciones = []
        return render_template("index.html", publicaciones=publicaciones)

    @app.get("/publicacion/<int:id_publicacion>")
    def detalle_publicacion(id_publicacion):
        publicacion = Publicacion.query.get_or_404(id_publicacion)
        return render_template("detalle.html", publicacion=publicacion)

    # ------------------------------------------------------------------
    # Publicar un producto (formulario publicacion.html)
    # ------------------------------------------------------------------
    @app.get("/publicacion.html")
    def publicacion():
        try:
            vendedores = (
                Usuario.query.filter_by(vendedor=True)
                .order_by(Usuario.nombre).all()
            )
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("Error al cargar vendedores.")
            vendedores = []
        return render_template("publicacion.html", vendedores=vendedores)

    @app.post("/api/publicaciones")
    def crear_publicacion():
        nombre = request.form.get("nombre", "").strip()
        categoria = request.form.get("categoria", "").strip()
        condicion = request.form.get("estado", "").strip()
        descripcion = request.form.get("descripcion", "").strip()

        # --- Validación (el front valida, pero el servidor NO se fía) ---
        if not nombre or len(nombre) > 100:
            return _error("El nombre es obligatorio (máximo 100 caracteres).")
        if categoria not in CATEGORIAS:
            return _error("Categoría inválida.")
        if condicion not in CONDICIONES:
            return _error("Estado del producto inválido.")
        if not descripcion or len(descripcion) > 1500:
            return _error("La descripción es obligatoria (máximo 1500 caracteres).")

        try:
            precio = Decimal(request.form.get("precio", "").strip())
            if not precio.is_finite() or precio <= 0 or precio > PRECIO_MAX:
                raise ValueError
        except (InvalidOperation, ValueError):
            return _error("Precio inválido.")

        try:
            stock = int(request.form.get("stock", "").strip())
            if not 1 <= stock <= 9999:
                raise ValueError
        except ValueError:
            return _error("El stock debe ser un entero entre 1 y 9999.")

        try:
            id_usuario = int(request.form.get("id_usuario", "").strip())
        except ValueError:
            return _error("Seleccioná un vendedor.")

        # --- Imagen (opcional) ---
        archivo = request.files.get("imagen")
        nombre_archivo = None
        ruta_archivo = None
        if archivo and archivo.filename:
            extension = _extension_imagen(archivo.stream.read(12))
            archivo.stream.seek(0)
            if extension is None:
                return _error("La imagen debe ser JPG, PNG o WEBP.")
            carpeta = os.path.join(current_app.static_folder, "uploads")
            os.makedirs(carpeta, exist_ok=True)
            nombre_archivo = f"{uuid.uuid4().hex}.{extension}"
            ruta_archivo = os.path.join(carpeta, nombre_archivo)

        # --- Guardado en la base de datos ---
        try:
            vendedor = db.session.get(Usuario, id_usuario)
            if vendedor is None or not vendedor.vendedor:
                return _error("El vendedor seleccionado no existe.")

            if ruta_archivo:
                archivo.save(ruta_archivo)

            producto = Producto(
                nombre=nombre,
                descripcion=descripcion,
                categoria=categoria,
                logo=(url_for("static", filename=f"uploads/{nombre_archivo}")
                      if nombre_archivo else None),
            )
            db.session.add(producto)
            db.session.flush()  # genera producto.id_producto

            nueva = Publicacion(
                producto=producto,
                vendedor=vendedor,
                stock=stock,
                precio=precio,
                condicion=condicion,
            )
            db.session.add(nueva)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            if ruta_archivo and os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)  # no dejar imágenes huérfanas
            current_app.logger.exception("Error al guardar la publicación.")
            return _error(
                "No se pudo guardar en la base de datos. Revisá la conexión.", 500
            )

        return jsonify(
            ok=True,
            id=nueva.id_publicacion,
            url=url_for("detalle_publicacion", id_publicacion=nueva.id_publicacion),
        ), 201

    # ------------------------------------------------------------------
    # Formulario antiguo (se mantiene tal cual)
    # ------------------------------------------------------------------
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