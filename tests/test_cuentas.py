"""Pruebas de registro, inicio/cierre de sesión y perfil de cuenta."""
import os
import re
import tempfile

import pytest
from werkzeug.security import check_password_hash

from gamemarket import create_app
from gamemarket.extensions import db
from gamemarket.models import Usuario


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


def token_csrf(client, path="/cuenta/registro"):
    response = client.get(path)
    assert response.status_code == 200
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match is not None
    return match.group(1).decode()


def test_registro_guarda_hash_y_crea_perfil(client):
    response = client.post("/cuenta/registro", data={
        "csrf_token": token_csrf(client),
        "nombre": "  Ada Lovelace  ",
        "email": "ADA@example.com",
        "contrasena": "clave-segura-123",
        "confirmacion": "clave-segura-123",
        "vendedor": "1",
        "admin": "1",
    })

    assert response.status_code == 302
    assert response.location.endswith("/cuenta/perfil")
    usuario = Usuario.query.one()
    assert usuario.nombre == "Ada Lovelace"
    assert usuario.email == "ada@example.com"
    assert usuario.contrasena != "clave-segura-123"
    assert check_password_hash(usuario.contrasena, "clave-segura-123")
    assert usuario.vendedor is True
    assert usuario.admin is False
    assert client.get("/cuenta/perfil").status_code == 200


@pytest.mark.parametrize("cambios", [
    {"nombre": ""},
    {"email": "correo-invalido"},
    {"contrasena": "corta"},
    {"confirmacion": "otra-clave"},
])
def test_registro_rechaza_datos_invalidos(client, cambios):
    datos = {
        "csrf_token": token_csrf(client),
        "nombre": "Usuario",
        "email": "usuario@example.com",
        "contrasena": "clave-segura-123",
        "confirmacion": "clave-segura-123",
    }
    datos.update(cambios)

    response = client.post("/cuenta/registro", data=datos)

    assert response.status_code == 200
    assert b"role=\"alert\"" in response.data
    assert Usuario.query.count() == 0


def test_registro_requiere_csrf(client):
    response = client.post("/cuenta/registro", data={
        "nombre": "Usuario",
        "email": "usuario@example.com",
        "contrasena": "clave-segura-123",
        "confirmacion": "clave-segura-123",
    })

    assert response.status_code == 400
    assert Usuario.query.count() == 0


def test_ingresar_y_salir(client):
    token = token_csrf(client)
    client.post("/cuenta/registro", data={
        "csrf_token": token,
        "nombre": "Usuario",
        "email": "usuario@example.com",
        "contrasena": "clave-segura-123",
        "confirmacion": "clave-segura-123",
    })
    client.post("/cuenta/salir", data={
        "csrf_token": token_csrf(client, "/cuenta/perfil"),
    })

    response = client.post("/cuenta/ingresar", data={
        "csrf_token": token_csrf(client, "/cuenta/ingresar"),
        "email": "USUARIO@example.com",
        "contrasena": "clave-segura-123",
    })

    assert response.status_code == 302
    assert response.location.endswith("/cuenta/perfil")
    assert client.get("/cuenta/perfil").status_code == 200

    token = token_csrf(client, "/cuenta/perfil")
    response = client.post("/cuenta/salir", data={"csrf_token": token})
    assert response.status_code == 302
    assert response.location.endswith("/index.html")
    assert client.get("/cuenta/perfil").status_code == 302


def test_ingreso_falla_con_credenciales_incorrectas(client):
    response = client.post("/cuenta/ingresar", data={
        "csrf_token": token_csrf(client, "/cuenta/ingresar"),
        "email": "nadie@example.com",
        "contrasena": "incorrecta",
    })

    assert response.status_code == 200
    assert b"El correo o la contrase" in response.data


def test_registro_rechaza_email_duplicado(client):
    token = token_csrf(client)
    payload = {
        "csrf_token": token,
        "nombre": "Usuario",
        "email": "usuario@example.com",
        "contrasena": "clave-segura-123",
        "confirmacion": "clave-segura-123",
    }
    client.post("/cuenta/registro", data=payload)
    client.post("/cuenta/salir", data={
        "csrf_token": token_csrf(client, "/cuenta/perfil"),
    })

    response = client.post("/cuenta/registro", data={
        **payload,
        "email": "USUARIO@example.com",
        "csrf_token": token_csrf(client),
    })

    assert response.status_code == 200
    assert b"Ya existe una cuenta" in response.data
    assert Usuario.query.count() == 1
