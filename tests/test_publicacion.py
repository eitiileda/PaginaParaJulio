"""Pruebas del alta de publicaciones (POST /api/publicaciones)."""
import io
import os
import tempfile

import pytest

from gamemarket import create_app
from gamemarket.extensions import db
from gamemarket.models import Usuario, Producto, Publicacion

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture()
def client():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    class TestConfig:
        TESTING = True
        SECRET_KEY = "test-only"
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_path
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        MAX_CONTENT_LENGTH = 6 * 1024 * 1024

    app = create_app(TestConfig)
    with app.app_context():
        db.session.add(Usuario(nombre="Vendedor", email="v@test.com", contrasena="x", vendedor=True))
        db.session.commit()
    with app.test_client() as c:
        yield c
    try:
        os.remove(db_path)
    except OSError:
        pass


def datos(**cambios):
    base = {
        "id_usuario": "1", "nombre": "Teclado RGB", "categoria": "perifericos",
        "estado": "Nuevo", "precio": "89999", "stock": "2",
        "descripcion": "Teclado mecánico",
    }
    base.update(cambios)
    return base


def test_publicar_sin_imagen(client):
    r = client.post("/api/publicaciones", data=datos())
    assert r.status_code == 201
    assert r.get_json()["ok"] is True
    assert Publicacion.query.count() == 1
    assert Producto.query.first().categoria == "perifericos"


def test_publicar_con_imagen(client):
    d = datos()
    d["imagen"] = (io.BytesIO(PNG), "foto.png")
    r = client.post("/api/publicaciones", data=d, content_type="multipart/form-data")
    assert r.status_code == 201
    logo = Producto.query.first().logo
    assert logo.startswith("/static/uploads/") and logo.endswith(".png")
    os.remove(os.path.join(client.application.static_folder, logo.removeprefix("/static/")))


def test_rechaza_archivo_que_no_es_imagen(client):
    d = datos()
    d["imagen"] = (io.BytesIO(b"MZ esto es un exe"), "foto.png")
    r = client.post("/api/publicaciones", data=d, content_type="multipart/form-data")
    assert r.status_code == 400
    assert Publicacion.query.count() == 0


@pytest.mark.parametrize("cambio", [
    {"nombre": ""}, {"categoria": "otra"}, {"estado": "Roto"},
    {"precio": "0"}, {"precio": "abc"}, {"precio": "999999999"},
    {"stock": "0"}, {"id_usuario": "999"}, {"descripcion": ""},
])
def test_rechaza_datos_invalidos(client, cambio):
    r = client.post("/api/publicaciones", data=datos(**cambio))
    assert r.status_code == 400
    assert Publicacion.query.count() == 0
