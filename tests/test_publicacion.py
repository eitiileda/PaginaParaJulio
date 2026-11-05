"""Pruebas del alta de publicaciones (POST /api/publicaciones)."""
import io
import os
import re
import tempfile

import pytest
from werkzeug.security import generate_password_hash

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
        db.session.add_all([
            Usuario(
                nombre="Vendedor", email="v@test.com",
                contrasena=generate_password_hash("password-vendedor"),
                vendedor=True,
            ),
            Usuario(
                nombre="Comprador", email="c@test.com",
                contrasena=generate_password_hash("password-comprador"),
                vendedor=False,
            ),
        ])
        db.session.commit()
    with app.test_client() as c:
        iniciar_sesion(c, "v@test.com", "password-vendedor")
        yield c
    try:
        os.remove(db_path)
    except OSError:
        pass


def token_csrf(client, path="/publicacion.html"):
    response = client.get(path)
    assert response.status_code == 200
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match is not None
    return match.group(1).decode()


def iniciar_sesion(client, email, contrasena, next_url=None):
    login_url = "/cuenta/ingresar"
    if next_url:
        login_url += "?next=" + next_url
    response = client.get(login_url)
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match is not None
    response = client.post(login_url, data={
        "csrf_token": match.group(1).decode(),
        "email": email,
        "contrasena": contrasena,
    })
    assert response.status_code == 302


def cerrar_sesion(client):
    response = client.get("/cuenta/perfil")
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match is not None
    return client.post("/cuenta/salir", data={
        "csrf_token": match.group(1).decode(),
    })


def datos(client, csrf_path="/publicacion.html", **cambios):
    base = {
        "csrf_token": token_csrf(client, csrf_path), "id_usuario": "2",
        "nombre": "Teclado RGB", "categoria": "perifericos",
        "estado": "Nuevo", "precio": "89999", "stock": "2",
        "descripcion": "Teclado mecánico",
    }
    base.update(cambios)
    return base


def test_publicar_sin_imagen(client):
    r = client.post("/api/publicaciones", data=datos(client))
    assert r.status_code == 201
    assert r.get_json()["ok"] is True
    assert Publicacion.query.count() == 1
    assert Producto.query.first().categoria == "perifericos"
    assert Publicacion.query.first().id_usuario == 1


def test_vendedor_vuelve_al_formulario_despues_de_ingresar(client):
    cerrar_sesion(client)
    response = client.get("/publicacion.html")
    assert response.status_code == 302
    login_url = response.location.replace("http://localhost", "")
    assert "next=/publicacion.html" in login_url

    response = client.get(login_url)
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match is not None
    response = client.post(login_url, data={
        "csrf_token": match.group(1).decode(),
        "email": "v@test.com",
        "contrasena": "password-vendedor",
    })

    assert response.status_code == 302
    assert response.location.endswith("/publicacion.html")


def test_publicar_con_imagen(client):
    d = datos(client)
    d["imagen"] = (io.BytesIO(PNG), "foto.png")
    r = client.post("/api/publicaciones", data=d, content_type="multipart/form-data")
    assert r.status_code == 201
    logo = Producto.query.first().logo
    assert logo.startswith("/static/uploads/") and logo.endswith(".png")
    os.remove(os.path.join(client.application.static_folder, logo.removeprefix("/static/")))


def test_rechaza_archivo_que_no_es_imagen(client):
    d = datos(client)
    d["imagen"] = (io.BytesIO(b"MZ esto es un exe"), "foto.png")
    r = client.post("/api/publicaciones", data=d, content_type="multipart/form-data")
    assert r.status_code == 400
    assert Publicacion.query.count() == 0


@pytest.mark.parametrize("cambio", [
    {"nombre": ""}, {"categoria": "otra"}, {"estado": "Roto"},
    {"precio": "0"}, {"precio": "abc"}, {"precio": "999999999"},
    {"stock": "0"}, {"descripcion": ""},
])
def test_rechaza_datos_invalidos(client, cambio):
    r = client.post("/api/publicaciones", data=datos(client, **cambio))
    assert r.status_code == 400
    assert Publicacion.query.count() == 0


def test_api_de_publicacion_requiere_sesion(client):
    cerrar_sesion(client)
    response = client.post("/api/publicaciones", data={
        "csrf_token": token_csrf(client, "/cuenta/ingresar"),
        **datos_base(),
    })

    assert response.status_code == 401
    assert response.get_json()["error"]
    assert Publicacion.query.count() == 0


def test_comprador_no_puede_publicar(client):
    cerrar_sesion(client)
    iniciar_sesion(client, "c@test.com", "password-comprador")

    response = client.post("/api/publicaciones", data=datos(
        client, csrf_path="/cuenta/perfil", **{"id_usuario": "1"},
    ))

    assert response.status_code == 403
    assert Publicacion.query.count() == 0


def test_comprador_puede_habilitar_ventas_y_publicar(client):
    cerrar_sesion(client)
    iniciar_sesion(client, "c@test.com", "password-comprador")
    response = client.get("/cuenta/perfil")
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match is not None

    response = client.post("/cuenta/habilitar-ventas", data={
        "csrf_token": match.group(1).decode(),
    })
    assert response.status_code == 302
    assert Usuario.query.filter_by(email="c@test.com").one().vendedor is True

    response = client.post("/api/publicaciones", data=datos(
        client, **{"id_usuario": "1"},
    ))
    assert response.status_code == 201
    assert Publicacion.query.one().id_usuario == 2


def test_formulario_antiguo_usa_el_usuario_autenticado(client):
    payload = {
        "csrf_token": token_csrf(client, "/upload.html"),
        "nombre": "Mouse RGB",
        "descripcion": "Mouse mecánico",
        "logo": "",
        "id_usuario": "2",
        "precio": "12000",
        "stock": "1",
        "descripcion_vendedor": "",
    }

    response = client.post("/upload.html", data=payload)

    assert response.status_code == 302
    assert Publicacion.query.one().id_usuario == 1


def datos_base():
    return {
        "nombre": "Teclado RGB", "categoria": "perifericos",
        "estado": "Nuevo", "precio": "89999", "stock": "2",
        "descripcion": "Teclado mecánico",
    }
