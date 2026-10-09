from decimal import Decimal, InvalidOperation

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder="html")

# --- Conexion a MySQL ---
DB_USER = "root"
DB_PASSWORD = "esc728"
DB_HOST = "localhost"
DB_NAME = "tienda_online"

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# --- Modelos: reflejan las tablas creadas por script.sql ---
class Usuario(db.Model):
    __tablename__ = "usuarios"
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    contrasena = db.Column(db.String(255), nullable=False)
    vendedor = db.Column(db.Boolean, default=True)
    admin = db.Column(db.Boolean, default=False)
    descripcion = db.Column(db.String(255))
    fecha_registro = db.Column(db.DateTime)
    logo = db.Column(db.String(255))


class Producto(db.Model):
    __tablename__ = "productos"
    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    logo = db.Column(db.String(255))


class Publicacion(db.Model):
    __tablename__ = "publicaciones"
    id_publicacion = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey("productos.id_producto"))
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario"))
    stock = db.Column(db.Integer, default=1)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.Enum("activo", "pausado", "finalizado"), default="activo")
    descripcion_vendedor = db.Column(db.String(255))
    valoracion = db.Column(db.Numeric(3, 2), default=5.00)
    fecha = db.Column(db.DateTime)

    producto = db.relationship("Producto", backref="publicaciones")
    vendedor = db.relationship("Usuario", backref="publicaciones")


class Compra(db.Model):
    __tablename__ = "compras"
    id_compra = db.Column(db.Integer, primary_key=True)
    id_publicacion = db.Column(db.Integer, db.ForeignKey("publicaciones.id_publicacion"))
    id_comprador = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario"))
    cantidad = db.Column(db.Integer, default=1)
    monto_total = db.Column(db.Numeric(10, 2), nullable=False)
    tit_tarjeta = db.Column(db.String(100))
    num_tarjeta = db.Column(db.String(30))
    fecha = db.Column(db.DateTime)


# --- Rutas ---
@app.route("/")
def index():
    publicaciones = (
        Publicacion.query.filter_by(estado="activo")
        .order_by(Publicacion.fecha.desc())
        .all()
    )
    return render_template("index.html", publicaciones=publicaciones)


@app.route("/publicacion/<int:id_publicacion>")
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
        id_usuario = request.form.get("id_usuario")
        stock_raw = request.form.get("stock", "")
        precio_raw = request.form.get("precio", "")

        PRECIO_MAXIMO = Decimal("99999999.99")  # limite de la columna DECIMAL(10,2)

        try:
            stock = int(stock_raw)
            precio = Decimal(precio_raw)
            if not nombre or not id_usuario or stock < 0 or precio <= 0:
                raise ValueError("datos incompletos")
            if precio > PRECIO_MAXIMO:
                raise ValueError("precio fuera de rango")
        except (ValueError, InvalidOperation):
            error = (
                "Revisa los datos: nombre, vendedor, stock y precio son obligatorios, "
                f"y el precio debe ser mayor a 0 y menor a {PRECIO_MAXIMO}."
            )
        else:
            try:
                producto = Producto(nombre=nombre, descripcion=descripcion, logo=logo)
                db.session.add(producto)
                db.session.flush()  # asigna id_producto antes de crear la publicacion

                publicacion = Publicacion(
                    id_producto=producto.id_producto,
                    id_usuario=id_usuario,
                    stock=stock,
                    precio=precio,
                    descripcion_vendedor=descripcion_vendedor,
                )
                db.session.add(publicacion)
                db.session.commit()
            except Exception:
                db.session.rollback()
                error = "No se pudo guardar el producto. Revisa los datos e intenta de nuevo."
            else:
                return redirect(url_for("index"))

    vendedores = Usuario.query.filter_by(vendedor=True).all()
    return render_template("upload.html", vendedores=vendedores, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
