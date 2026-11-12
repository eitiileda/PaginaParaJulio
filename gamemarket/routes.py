"""Rutas web. Cada página queda separada para poder añadir módulos gradualmente."""
import os
import re
import uuid
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from flask import (
    render_template, request, redirect, url_for, current_app, jsonify, session,
    flash, abort,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .models import Usuario, Producto, Publicacion, Compra


# "publicacion.html" ya NO está acá: tiene su propia ruta más abajo,
# porque necesita cargar la lista de vendedores desde la base de datos.
PAGINAS = {
    "busqueda.html": "busqueda.html",
    "categorias.html": "categorias.html",
    "tal_categoria.html": "tal_categoria.html",
    "producto.html": "producto.html",
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
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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


def _redirigir_local_si_corresponde(destino):
    partes = urlsplit(destino or "")
    if (
        destino.startswith("/")
        and not destino.startswith("//")
        and "\\" not in destino
        and not partes.scheme
        and not partes.netloc
    ):
        return redirect(destino)
    return redirect(url_for("perfil"))


def _limpiar_sesion_manteniendo_carrito():
    carrito = session.get("carrito", {})
    session.clear()
    if carrito:
        session["carrito"] = carrito


def _leer_carrito():
    carrito = session.get("carrito", {})
    if not isinstance(carrito, dict):
        return {}
    items = {}
    for id_publicacion, cantidad in carrito.items():
        try:
            id_validado = int(id_publicacion)
            cantidad_validada = int(cantidad)
        except (TypeError, ValueError):
            continue
        if id_validado > 0 and 1 <= cantidad_validada <= 999:
            items[id_validado] = cantidad_validada
    return items


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
                Publicacion.query.filter_by(estado="activo")
                .filter(Publicacion.stock > 0)
                .order_by(Publicacion.fecha.desc())
                .limit(12)
                .all()
            )
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("Error al listar publicaciones.")
            publicaciones = []
        return render_template("index.html", publicaciones=publicaciones)

    @app.route("/cuenta/registro", methods=["GET", "POST"])
    def registro():
        if current_user.is_authenticated:
            return _redirigir_local_si_corresponde(
                request.args.get("next", "")
            )

        error = None
        datos = {"nombre": "", "email": ""}
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            email = request.form.get("email", "").strip().lower()
            contrasena = request.form.get("contrasena", "")
            confirmacion = request.form.get("confirmacion", "")
            datos = {"nombre": nombre, "email": email}

            if not nombre or len(nombre) > 100:
                error = "El nombre es obligatorio (máximo 100 caracteres)."
            elif len(email) > 150 or not EMAIL_RE.fullmatch(email):
                error = "Ingresá un correo electrónico válido."
            elif len(contrasena) < 8 or len(contrasena) > 128:
                error = "La contraseña debe tener entre 8 y 128 caracteres."
            elif contrasena != confirmacion:
                error = "Las contraseñas no coinciden."
            else:
                try:
                    if Usuario.query.filter_by(email=email).first() is not None:
                        error = "Ya existe una cuenta con ese correo."
                    else:
                        usuario = Usuario(
                            nombre=nombre,
                            email=email,
                            contrasena=generate_password_hash(contrasena),
                            vendedor=request.form.get("vendedor") == "1",
                            admin=False,
                        )
                        db.session.add(usuario)
                        db.session.commit()
                        _limpiar_sesion_manteniendo_carrito()
                        login_user(usuario)
                        return _redirigir_local_si_corresponde(
                            request.args.get("next", "")
                        )
                except IntegrityError:
                    db.session.rollback()
                    error = "Ya existe una cuenta con ese correo."
                except SQLAlchemyError:
                    db.session.rollback()
                    current_app.logger.exception("Error al crear una cuenta.")
                    error = "No se pudo crear la cuenta. Intentá nuevamente."

        return render_template(
            "cuenta_registro.html",
            error=error,
            datos=datos,
            next_url=request.args.get("next", ""),
        )

    @app.route("/cuenta/ingresar", methods=["GET", "POST"])
    def iniciar_sesion():
        if current_user.is_authenticated:
            return redirect(url_for("perfil"))

        error = None
        email = ""
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            contrasena = request.form.get("contrasena", "")
            try:
                usuario = Usuario.query.filter_by(email=email).first()
            except SQLAlchemyError:
                db.session.rollback()
                current_app.logger.exception("Error al buscar una cuenta.")
                error = "No se pudo iniciar sesión. Intentá nuevamente."
            else:
                try:
                    contrasena_valida = (
                        usuario is not None
                        and check_password_hash(usuario.contrasena, contrasena)
                    )
                except (TypeError, ValueError):
                    current_app.logger.warning(
                        "Hash de contraseña inválido para el usuario %s.",
                        usuario.id_usuario,
                    )
                    contrasena_valida = False

                if not contrasena_valida:
                    error = "El correo o la contraseña no son correctos."
                else:
                    _limpiar_sesion_manteniendo_carrito()
                    login_user(usuario)
                    return _redirigir_local_si_corresponde(
                        request.args.get("next", "")
                    )

        return render_template("cuenta_ingresar.html", error=error, email=email)

    @app.post("/cuenta/salir")
    @login_required
    def cerrar_sesion():
        logout_user()
        return redirect(url_for("index"))

    @app.get("/cuenta/perfil")
    @login_required
    def perfil():
        return render_template("cuenta_perfil.html", usuario=current_user)

    @app.get("/carrito.html")
    def carrito():
        items = _leer_carrito()
        publicaciones = {}
        if items:
            publicaciones = {
                publicacion.id_publicacion: publicacion
                for publicacion in Publicacion.query.filter(
                    Publicacion.id_publicacion.in_(items)
                ).all()
            }
        lineas = [
            {
                "publicacion": publicaciones.get(id_publicacion),
                "id_publicacion": id_publicacion,
                "cantidad": cantidad,
            }
            for id_publicacion, cantidad in items.items()
        ]
        total = sum(
            (linea["publicacion"].precio * linea["cantidad"]
             for linea in lineas
             if linea["publicacion"]
             and linea["publicacion"].estado == "activo"
             and linea["publicacion"].stock >= linea["cantidad"]),
            Decimal("0.00"),
        )
        puede_confirmar = all(
            linea["publicacion"] is not None
            and linea["publicacion"].estado == "activo"
            and linea["publicacion"].stock >= linea["cantidad"]
            and (
                not current_user.is_authenticated
                or linea["publicacion"].id_usuario != current_user.id_usuario
            )
            for linea in lineas
        )
        return render_template(
            "carrito.html",
            lineas=lineas,
            total=total,
            puede_confirmar=puede_confirmar,
        )

    @app.post("/carrito/agregar/<int:id_publicacion>")
    def agregar_al_carrito(id_publicacion):
        publicacion = db.session.get(Publicacion, id_publicacion)
        if publicacion is None:
            abort(404)
        if publicacion.estado != "activo" or publicacion.stock < 1:
            flash("Este producto no está disponible para agregar al carrito.", "error")
            return redirect(url_for("detalle_publicacion", id_publicacion=id_publicacion))

        try:
            cantidad = int(request.form.get("cantidad", "1"))
        except (TypeError, ValueError):
            flash("La cantidad seleccionada no es válida.", "error")
            return redirect(url_for("detalle_publicacion", id_publicacion=id_publicacion))
        if not 1 <= cantidad <= min(publicacion.stock, 999):
            flash("La cantidad supera el stock disponible.", "error")
            return redirect(url_for("detalle_publicacion", id_publicacion=id_publicacion))

        items = _leer_carrito()
        cantidad_total = items.get(id_publicacion, 0) + cantidad
        if cantidad_total > min(publicacion.stock, 999):
            flash("No hay suficiente stock para esa cantidad.", "error")
        else:
            items[id_publicacion] = cantidad_total
            if len(items) > 30:
                flash("El carrito admite hasta 30 productos diferentes.", "error")
                return redirect(url_for("detalle_publicacion", id_publicacion=id_publicacion))
            session["carrito"] = {
                str(id_item): qty for id_item, qty in items.items()
            }
            flash("Producto agregado al carrito.", "success")
            return redirect(url_for("carrito"))
        return redirect(url_for("detalle_publicacion", id_publicacion=id_publicacion))

    @app.post("/carrito/actualizar/<int:id_publicacion>")
    def actualizar_carrito(id_publicacion):
        items = _leer_carrito()
        if id_publicacion not in items:
            flash("Ese producto ya no está en el carrito.", "error")
            return redirect(url_for("carrito"))

        try:
            cantidad = int(request.form.get("cantidad", ""))
        except (TypeError, ValueError):
            cantidad = 0

        publicacion = db.session.get(Publicacion, id_publicacion)
        if cantidad == 0:
            items.pop(id_publicacion)
            flash("Producto eliminado del carrito.", "success")
        elif (
            publicacion is None
            or publicacion.estado != "activo"
            or not 1 <= cantidad <= min(publicacion.stock, 999)
        ):
            flash("La cantidad no es válida para el stock disponible.", "error")
        else:
            items[id_publicacion] = cantidad
            flash("Carrito actualizado.", "success")

        session["carrito"] = {str(item_id): qty for item_id, qty in items.items()}
        return redirect(url_for("carrito"))

    @app.post("/carrito/confirmar")
    @login_required
    def confirmar_compra():
        items = _leer_carrito()
        if not items:
            flash("Tu carrito está vacío.", "error")
            return redirect(url_for("carrito"))

        try:
            publicaciones = (
                Publicacion.query
                .filter(Publicacion.id_publicacion.in_(items))
                .order_by(Publicacion.id_publicacion)
                .with_for_update()
                .all()
            )
            por_id = {p.id_publicacion: p for p in publicaciones}

            if len(por_id) != len(items):
                raise ValueError("Hay un producto del carrito que ya no existe.")

            compras = []
            for id_publicacion, cantidad in items.items():
                publicacion = por_id[id_publicacion]
                if publicacion.estado != "activo" or publicacion.stock < cantidad:
                    raise ValueError(
                        f"No hay stock suficiente de {publicacion.producto.nombre}."
                    )
                if publicacion.id_usuario == current_user.id_usuario:
                    raise ValueError("No podés comprar una publicación propia.")

                compra = Compra(
                    id_publicacion=id_publicacion,
                    id_comprador=current_user.id_usuario,
                    cantidad=cantidad,
                    monto_total=publicacion.precio * cantidad,
                )
                compras.append(compra)
                publicacion.stock -= cantidad

            db.session.add_all(compras)
            db.session.commit()
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "error")
            return redirect(url_for("carrito"))
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("Error al confirmar la compra del usuario %s.", current_user.id_usuario)
            flash("No se pudo confirmar la compra. Intentá nuevamente.", "error")
            return redirect(url_for("carrito"))

        session.pop("carrito", None)
        flash(
            "Compra registrada. Esta versión no procesa pagos; no se realizó ningún cobro.",
            "success",
        )
        return redirect(url_for("carrito"))

    @app.post("/cuenta/habilitar-ventas")
    @login_required
    def habilitar_ventas():
        current_user.vendedor = True
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("Error al habilitar ventas para una cuenta.")
            return "No se pudo habilitar la cuenta vendedora.", 500
        return redirect(url_for("perfil"))

    @app.get("/cuenta/publicaciones")
    @login_required
    def mis_publicaciones():
        if not current_user.vendedor:
            return redirect(url_for("perfil"))
        publicaciones = (
            Publicacion.query
            .filter_by(id_usuario=current_user.id_usuario)
            .order_by(Publicacion.fecha.desc())
            .all()
        )
        return render_template(
            "mis_publicaciones.html",
            publicaciones=publicaciones,
        )

    @app.route(
        "/cuenta/publicaciones/<int:id_publicacion>/editar",
        methods=["GET", "POST"],
    )
    @login_required
    def editar_publicacion(id_publicacion):
        if not current_user.vendedor:
            return redirect(url_for("perfil"))
        publicacion = Publicacion.query.filter_by(
            id_publicacion=id_publicacion,
            id_usuario=current_user.id_usuario,
        ).first_or_404()

        if publicacion.estado == "finalizado":
            return redirect(url_for("mis_publicaciones"))

        error = None
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            categoria = request.form.get("categoria", "").strip()
            condicion = request.form.get("condicion", "").strip()
            descripcion = request.form.get("descripcion", "").strip()

            if not nombre or len(nombre) > 100:
                error = "El nombre es obligatorio (máximo 100 caracteres)."
            elif categoria not in CATEGORIAS:
                error = "Categoría inválida."
            elif condicion not in CONDICIONES:
                error = "Estado del producto inválido."
            elif not descripcion or len(descripcion) > 1500:
                error = "La descripción es obligatoria (máximo 1500 caracteres)."

            try:
                precio = Decimal(request.form.get("precio", "").strip())
                if not precio.is_finite() or precio <= 0 or precio > PRECIO_MAX:
                    raise ValueError
            except (InvalidOperation, ValueError):
                error = error or "Precio inválido."

            try:
                stock = int(request.form.get("stock", "").strip())
                if not 0 <= stock <= 9999:
                    raise ValueError
            except ValueError:
                error = error or "El stock debe ser un entero entre 0 y 9999."

            if error is None:
                publicacion.producto.nombre = nombre
                publicacion.producto.categoria = categoria
                publicacion.producto.descripcion = descripcion
                publicacion.condicion = condicion
                publicacion.precio = precio
                publicacion.stock = stock
                try:
                    db.session.commit()
                    return redirect(url_for("mis_publicaciones"))
                except SQLAlchemyError:
                    db.session.rollback()
                    current_app.logger.exception(
                        "Error al actualizar la publicación %s.",
                        id_publicacion,
                    )
                    error = "No se pudo guardar los cambios. Intentá nuevamente."

        return render_template(
            "editar_publicacion.html",
            publicacion=publicacion,
            error=error,
            categorias=sorted(CATEGORIAS),
            condiciones=sorted(CONDICIONES),
            valores=request.form if request.method == "POST" else {},
        )

    @app.post("/cuenta/publicaciones/<int:id_publicacion>/estado")
    @login_required
    def cambiar_estado_publicacion(id_publicacion):
        if not current_user.vendedor:
            return redirect(url_for("perfil"))
        publicacion = Publicacion.query.filter_by(
            id_publicacion=id_publicacion,
            id_usuario=current_user.id_usuario,
        ).first_or_404()
        accion = request.form.get("accion")

        if publicacion.estado == "finalizado":
            return _error("Una publicación finalizada no se puede reactivar.", 409)
        if accion == "pausar" and publicacion.estado == "activo":
            publicacion.estado = "pausado"
        elif (
            accion == "activar"
            and publicacion.estado == "pausado"
            and publicacion.stock > 0
        ):
            publicacion.estado = "activo"
        elif accion == "finalizar":
            publicacion.estado = "finalizado"
        else:
            return _error("No se puede realizar ese cambio de estado.", 400)

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception(
                "Error al cambiar el estado de la publicación %s.",
                id_publicacion,
            )
            return _error("No se pudo actualizar el estado. Intentá nuevamente.", 500)
        return redirect(url_for("mis_publicaciones"))

    @app.get("/publicacion/<int:id_publicacion>")
    def detalle_publicacion(id_publicacion):
        publicacion = db.session.get(Publicacion, id_publicacion)
        if publicacion is None:
            abort(404)
        return render_template("detalle.html", publicacion=publicacion)

    # ------------------------------------------------------------------
    # Publicar un producto (formulario publicacion.html)
    # ------------------------------------------------------------------
    @app.get("/publicacion.html")
    @login_required
    def publicacion():
        if not current_user.vendedor:
            return redirect(url_for("perfil"))
        return render_template("publicacion.html")

    @app.post("/api/publicaciones")
    @login_required
    def crear_publicacion():
        if not current_user.vendedor:
            return _error("Activá el modo vendedor para publicar productos.", 403)

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
                vendedor=current_user,
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
    @login_required
    def upload():
        if not current_user.vendedor:
            return redirect(url_for("perfil"))

        error = None
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            descripcion = request.form.get("descripcion", "").strip()
            logo = request.form.get("logo", "").strip() or None
            descripcion_vendedor = request.form.get("descripcion_vendedor", "").strip()
            stock_raw = request.form.get("stock", "1").strip()
            precio_raw = request.form.get("precio", "").strip()

            try:
                stock = int(stock_raw)
                precio = Decimal(precio_raw)
                if not nombre or stock < 1 or stock > 9999 or precio <= 0 or not precio.is_finite():
                    raise ValueError
                if precio > Decimal("99999999.99"):
                    raise ValueError
            except (ValueError, InvalidOperation):
                error = "Revisá el nombre, stock y precio. El stock debe ser mayor a cero y el precio debe ser válido."
            else:
                try:
                    producto = Producto(nombre=nombre, descripcion=descripcion, logo=logo)
                    db.session.add(producto)
                    db.session.flush()
                    publicacion = Publicacion(
                        producto=producto,
                        vendedor=current_user,
                        stock=stock,
                        precio=precio,
                        descripcion_vendedor=descripcion_vendedor,
                    )
                    db.session.add(publicacion)
                    db.session.commit()
                    return redirect(url_for("index"))
                except SQLAlchemyError:
                    db.session.rollback()
                    current_app.logger.exception("Error al guardar una publicación.")
                    error = "No se pudo guardar el producto. Revisá la conexión y la base de datos."

        return render_template("upload.html", error=error)

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