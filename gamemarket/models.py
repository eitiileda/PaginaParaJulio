"""Modelos iniciales. Reflejan las tablas principales de la base de datos."""
from .extensions import db


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    contrasena = db.Column(db.String(255), nullable=False)  # Guardar hash, nunca texto plano.
    vendedor = db.Column(db.Boolean, default=True, nullable=False)
    admin = db.Column(db.Boolean, default=False, nullable=False)
    descripcion = db.Column(db.String(255))
    fecha_registro = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    logo = db.Column(db.String(255), default="default_avatar.png")

    publicaciones = db.relationship("Publicacion", back_populates="vendedor")


class Producto(db.Model):
    __tablename__ = "productos"

    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    logo = db.Column(db.String(255))

    publicaciones = db.relationship("Publicacion", back_populates="producto")


class Publicacion(db.Model):
    __tablename__ = "publicaciones"

    id_publicacion = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey("productos.id_producto", ondelete="CASCADE"), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    stock = db.Column(db.Integer, default=1, nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.Enum("activo", "pausado", "finalizado", name="estado_publicacion"), default="activo")
    descripcion_vendedor = db.Column(db.String(255))
    valoracion = db.Column(db.Numeric(3, 2), default=5.00)
    fecha = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    producto = db.relationship("Producto", back_populates="publicaciones")
    vendedor = db.relationship("Usuario", back_populates="publicaciones")


class Compra(db.Model):
    __tablename__ = "compras"

    id_compra = db.Column(db.Integer, primary_key=True)
    id_publicacion = db.Column(db.Integer, db.ForeignKey("publicaciones.id_publicacion"), nullable=False)
    id_comprador = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario"), nullable=False)
    cantidad = db.Column(db.Integer, default=1, nullable=False)
    monto_total = db.Column(db.Numeric(10, 2), nullable=False)
    # No guardar números de tarjeta: integrar una pasarela de pago cuando corresponda.
    referencia_pago = db.Column(db.String(255))
    fecha = db.Column(db.DateTime, server_default=db.func.current_timestamp())
