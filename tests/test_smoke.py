"""Pruebas de humo para comprobar que las rutas principales responden."""
import os
import tempfile

import pytest

from gamemarket import create_app


@pytest.fixture()
def client():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    class TestConfig:
        TESTING = True
        SECRET_KEY = "test-only"
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_path
        SQLALCHEMY_TRACK_MODIFICATIONS = False

    app = create_app(TestConfig)
    with app.test_client() as test_client:
        yield test_client

    try:
        os.remove(db_path)
    except OSError:
        pass


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.parametrize("path", [
    "/index.html",
    "/busqueda.html",
    "/categorias.html",
    "/tal_categoria.html",
    "/producto.html",
    "/carrito.html",
    "/historial.html",
    "/mas_opciones.html",
    "/ofertas.html",
    "/publicacion.html",
    "/chats.html",
])
def test_prototype_pages_load(client, path):
    response = client.get(path)
    assert response.status_code == 200


def test_detail_without_id_returns_home(client):
    response = client.get("/detalle.html")
    assert response.status_code == 302
