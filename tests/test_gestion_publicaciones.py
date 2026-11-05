"""Pruebas del panel de gestión de publicaciones del vendedor."""
import os
import re
import tempfile

import pytest
from werkzeug.security import generate_password_hash

from gamemarket import create_app
from gamemarket.extensions import db
from gamemarket.models import Producto, Publicacion, Usuario


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
    with app.app_context():
        db.session.add_all([
            Usuario(
                nombre="Vendedora", email="vendedora@example.com",
                contrasena=generate_password_hash("password-vendedora"),
                vendedor=True,
            ),
            Usuario(
                nombre="Otro vendedor", email="otro@example.com",
                contrasena=generate_password_hash("password-otro"),
                vendedor=True,
            ),
        ])
        db.session.commit()
        producto = Producto(
            nombre="Consola propia",
            descripcion="Descripción original",
            categoria="consolas",
        )
        producto_ajeno = Producto(
            nombre="Producto ajeno",
            descripcion="Descripción ajena",
            categoria="videojuegos",
        )
        db.session.add_all([producto, producto_ajeno])
        db.session.flush()
        db.session.add_all([
            Publicacion(
                producto=producto,
                id_usuario=1,
                stock=3,
                precio=150000,
                estado="activo",
                condicion="Usado",
            ),
            Publicacion(
                producto=producto_ajeno,
                id_usuario=2,
                stock=4,
                precio=20000,
                estado="activo",
                condicion="Nuevo",
            ),
        ])
        db.session.commit()

    with app.test_client() as test_client:
        iniciar_sesion(test_client)
        yield test_client

    try:
        os.remove(db_path)
    except OSError:
        pass


def iniciar_sesion(client, email="vendedora@example.com", contrasena="password-vendedora"):
    response = client.get("/cuenta/ingresar")
    token = extraer_token(response.data)
    response = client.post("/cuenta/ingresar", data={
        "csrf_token": token,
        "email": email,
        "contrasena": contrasena,
    })
    assert response.status_code == 302


def extraer_token(html):
    match = re.search(rb'name="csrf_token" value="([^"]+)"', html)
    assert match is not None
    return match.group(1).decode()


def token_del_panel(client):
    response = client.get("/cuenta/publicaciones")
    assert response.status_code == 200
    return extraer_token(response.data), response.data


def test_panel_muestra_solo_publicaciones_propias(client):
    _token, html = token_del_panel(client)
    assert b"Consola propia" in html
    assert b"Producto ajeno" not in html


def test_editar_publicacion_actualiza_producto_y_aviso(client):
    response = client.get("/cuenta/publicaciones/1/editar")
    assert response.status_code == 200
    token = extraer_token(response.data)

    response = client.post("/cuenta/publicaciones/1/editar", data={
        "csrf_token": token,
        "nombre": "Consola actualizada",
        "categoria": "consolas",
        "condicion": "Nuevo",
        "descripcion": "Nueva descripción",
        "precio": "175000.50",
        "stock": "7",
    })

    assert response.status_code == 302
    publicacion = db.session.get(Publicacion, 1)
    assert publicacion.producto.nombre == "Consola actualizada"
    assert publicacion.producto.descripcion == "Nueva descripción"
    assert publicacion.precio == 175000.50
    assert publicacion.stock == 7
    assert publicacion.condicion == "Nuevo"


def test_editar_publicacion_rechaza_datos_invalidos(client):
    response = client.get("/cuenta/publicaciones/1/editar")
    token = extraer_token(response.data)
    response = client.post("/cuenta/publicaciones/1/editar", data={
        "csrf_token": token,
        "nombre": "Consola actualizada",
        "categoria": "inventada",
        "condicion": "Nuevo",
        "descripcion": "Descripción",
        "precio": "0",
        "stock": "10000",
    })

    assert response.status_code == 200
    assert b'role="alert"' in response.data
    publicacion = db.session.get(Publicacion, 1)
    assert publicacion.producto.nombre == "Consola propia"
    assert publicacion.precio == 150000


@pytest.mark.parametrize("endpoint", [
    "/cuenta/publicaciones/2/editar",
    "/cuenta/publicaciones/2/estado",
])
def test_no_se_puede_administrar_publicacion_ajena(client, endpoint):
    if endpoint.endswith("/estado"):
        token, _ = token_del_panel(client)
        response = client.post(endpoint, data={
            "csrf_token": token,
            "accion": "finalizar",
        })
    else:
        response = client.get(endpoint)

    assert response.status_code == 404
    assert db.session.get(Publicacion, 2).estado == "activo"


def test_pausar_activar_y_finalizar_publicacion(client):
    token, _ = token_del_panel(client)
    response = client.post("/cuenta/publicaciones/1/estado", data={
        "csrf_token": token,
        "accion": "pausar",
    })
    assert response.status_code == 302
    assert db.session.get(Publicacion, 1).estado == "pausado"

    token, _ = token_del_panel(client)
    response = client.post("/cuenta/publicaciones/1/estado", data={
        "csrf_token": token,
        "accion": "activar",
    })
    assert response.status_code == 302
    assert db.session.get(Publicacion, 1).estado == "activo"

    token, _ = token_del_panel(client)
    response = client.post("/cuenta/publicaciones/1/estado", data={
        "csrf_token": token,
        "accion": "finalizar",
    })
    assert response.status_code == 302
    assert db.session.get(Publicacion, 1).estado == "finalizado"

    response = client.post("/cuenta/publicaciones/1/estado", data={
        "csrf_token": token,
        "accion": "activar",
    })
    assert response.status_code == 409
    assert db.session.get(Publicacion, 1).estado == "finalizado"
    assert client.get("/cuenta/publicaciones/1/editar").status_code == 302


def test_vendedor_sin_stock_no_puede_activar_publicacion(client):
    publicacion = db.session.get(Publicacion, 1)
    publicacion.estado = "pausado"
    publicacion.stock = 0
    db.session.commit()
    token, _ = token_del_panel(client)

    response = client.post("/cuenta/publicaciones/1/estado", data={
        "csrf_token": token,
        "accion": "activar",
    })

    assert response.status_code == 400
    assert db.session.get(Publicacion, 1).estado == "pausado"


def test_catalogo_principal_no_muestra_avisos_no_disponibles(client):
    publicacion = db.session.get(Publicacion, 1)
    publicacion.estado = "pausado"
    db.session.get(Publicacion, 2).stock = 0
    db.session.commit()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Consola propia" not in response.data
    assert b"Producto ajeno" not in response.data
