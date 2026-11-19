"""Pruebas del carrito de sesión y la confirmación de compras."""
import os
import re
import tempfile
from decimal import Decimal

import pytest
from werkzeug.security import generate_password_hash

from gamemarket import create_app
from gamemarket.extensions import db
from gamemarket.models import Compra, Producto, Publicacion, Usuario


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
                nombre="Compradora", email="compradora@example.com",
                contrasena=generate_password_hash("password-compradora"),
                vendedor=False,
            ),
            Usuario(
                nombre="Vendedor", email="vendedor@example.com",
                contrasena=generate_password_hash("password-vendedor"),
                vendedor=True,
            ),
        ])
        db.session.commit()
        productos = [
            Producto(nombre="Control", descripcion="Control gamer", categoria="accesorios"),
            Producto(nombre="Auriculares", descripcion="Audio gamer", categoria="audio"),
            Producto(nombre="Producto propio", descripcion="De la compradora", categoria="pc"),
        ]
        db.session.add_all(productos)
        db.session.flush()
        db.session.add_all([
            Publicacion(
                producto=productos[0], id_usuario=2, stock=5,
                precio=Decimal("10000.00"), estado="activo", condicion="Nuevo",
            ),
            Publicacion(
                producto=productos[1], id_usuario=2, stock=2,
                precio=Decimal("2500.50"), estado="activo", condicion="Usado",
            ),
            Publicacion(
                producto=productos[2], id_usuario=1, stock=4,
                precio=Decimal("5000.00"), estado="activo", condicion="Nuevo",
            ),
        ])
        db.session.commit()

    with app.test_client() as test_client:
        yield test_client

    try:
        os.remove(db_path)
    except OSError:
        pass


def extraer_token(response):
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match is not None
    return match.group(1).decode()


def token_detalle(client, id_publicacion=1):
    response = client.get(f"/publicacion/{id_publicacion}")
    assert response.status_code == 200
    return extraer_token(response)


def agregar(client, id_publicacion=1, cantidad=1):
    return client.post(
        f"/carrito/agregar/{id_publicacion}",
        data={
            "csrf_token": token_detalle(client, id_publicacion),
            "cantidad": str(cantidad),
        },
    )


def ingresar(client):
    response = client.get("/cuenta/ingresar")
    response = client.post("/cuenta/ingresar", data={
        "csrf_token": extraer_token(response),
        "email": "compradora@example.com",
        "contrasena": "password-compradora",
    })
    assert response.status_code == 302


def test_carrito_invita_a_explorar_si_esta_vacio(client):
    response = client.get("/carrito.html")
    assert response.status_code == 200
    assert b"Tu carrito est\xc3\xa1 vac\xc3\xado" in response.data


def test_visitante_agrega_y_actualiza_productos_en_el_carrito(client):
    response = agregar(client, cantidad=2)
    assert response.status_code == 302
    assert response.location.endswith("/carrito.html")
    agregar(client, id_publicacion=2, cantidad=1)

    response = client.get("/carrito.html")
    assert b"Control" in response.data
    assert b"Auriculares" in response.data
    assert "🪙 20.000".encode() in response.data
    assert "🪙 2.500,50".encode() in response.data

    response = client.post("/carrito/actualizar/1", data={
        "csrf_token": extraer_token(response),
        "cantidad": "3",
    })
    assert response.status_code == 302
    response = client.get("/carrito.html")
    assert "🪙 30.000".encode() in response.data

    response = client.post("/carrito/actualizar/1", data={
        "csrf_token": extraer_token(response),
        "cantidad": "0",
    })
    assert response.status_code == 302
    response = client.get("/carrito.html")
    assert b"Control" not in response.data
    assert b"Auriculares" in response.data


def test_carrito_rechaza_cantidad_mayor_al_stock(client):
    response = agregar(client, cantidad=6)
    assert response.status_code == 302
    response = client.get("/carrito.html")
    assert b"Tu carrito est\xc3\xa1 vac\xc3\xado" in response.data


def test_confirmar_requiere_ingresar_y_preserva_el_carrito(client):
    agregar(client, cantidad=2)
    response = client.get("/carrito.html")
    response = client.post("/carrito/confirmar", data={
        "csrf_token": extraer_token(response),
    })

    assert response.status_code == 302
    assert response.location.endswith("/cuenta/ingresar?next=/carrito.html")
    login_url = response.location
    response = client.get(login_url)
    response = client.post(login_url, data={
        "csrf_token": extraer_token(response),
        "email": "compradora@example.com",
        "contrasena": "password-compradora",
    })
    assert response.status_code == 302
    assert response.location.endswith("/carrito.html")
    response = client.get("/carrito.html")
    assert b"Control" in response.data


def test_carrito_se_conserva_al_registrarse_desde_el_checkout(client):
    agregar(client, cantidad=1)
    response = client.get("/cuenta/registro?next=/carrito.html")
    response = client.post("/cuenta/registro?next=/carrito.html", data={
        "csrf_token": extraer_token(response),
        "nombre": "Nueva compradora",
        "email": "nueva@example.com",
        "contrasena": "password-nueva",
        "confirmacion": "password-nueva",
    })

    assert response.status_code == 302
    assert response.location.endswith("/carrito.html")
    assert b"Control" in client.get("/carrito.html").data


def test_confirmar_compra_registra_compra_y_descuenta_stock(client):
    agregar(client, cantidad=2)
    agregar(client, id_publicacion=2, cantidad=1)
    ingresar(client)

    response = client.get("/carrito.html")
    response = client.post("/carrito/confirmar", data={
        "csrf_token": extraer_token(response),
    })

    assert response.status_code == 302
    assert response.location.endswith("/cuenta/compras")
    compras = Compra.query.order_by(Compra.id_publicacion).all()
    assert len(compras) == 2
    assert [compra.referencia_pago for compra in compras] == ["monedas", "monedas"]
    assert [compra.id_comprador for compra in compras] == [1, 1]
    assert [compra.cantidad for compra in compras] == [2, 1]
    assert [compra.monto_total for compra in compras] == [
        Decimal("20000.00"), Decimal("2500.50"),
    ]
    assert db.session.get(Publicacion, 1).stock == 3
    assert db.session.get(Publicacion, 2).stock == 1

    response = client.get("/cuenta/compras")
    assert "Pagaste 22.500,50 monedas".encode() in response.data
    assert b"Control" in response.data
    assert b"Auriculares" in response.data

    response = client.get("/carrito.html")
    assert b"Tu carrito est\xc3\xa1 vac\xc3\xado" in response.data


def test_confirmar_revalida_stock_y_no_crea_compra_parcial(client):
    agregar(client, cantidad=2)
    agregar(client, id_publicacion=2, cantidad=2)
    ingresar(client)
    db.session.get(Publicacion, 2).stock = 1
    db.session.commit()

    response = client.get("/carrito.html")
    response = client.post("/carrito/confirmar", data={
        "csrf_token": extraer_token(response),
    })

    assert response.status_code == 302
    assert Compra.query.count() == 0
    assert db.session.get(Publicacion, 1).stock == 5
    assert db.session.get(Publicacion, 2).stock == 1
    assert b"stock suficiente" in client.get("/carrito.html").data


def test_no_se_puede_comprar_publicacion_propia(client):
    agregar(client, id_publicacion=3)
    ingresar(client)

    response = client.get("/carrito.html")
    response = client.post("/carrito/confirmar", data={
        "csrf_token": extraer_token(response),
    })

    assert response.status_code == 302
    assert Compra.query.count() == 0
    assert db.session.get(Publicacion, 3).stock == 4
    assert b"publicaci\xc3\xb3n propia" in client.get("/carrito.html").data


def test_vendedor_no_ve_boton_ni_puede_agregar_su_propio_producto(client):
    ingresar(client)  # la compradora (id 1) es dueña de la publicación 3

    detalle = client.get("/publicacion/3")
    assert detalle.status_code == 200
    assert b"Agregar al carrito" not in detalle.data
    assert "Esta es tu publicación".encode() in detalle.data

    # Aunque arme el POST a mano, el servidor lo rechaza.
    token = extraer_token(client.get("/cuenta/perfil"))
    response = client.post(
        "/carrito/agregar/3",
        data={"cantidad": 1, "csrf_token": token},
    )
    assert response.status_code == 302
    assert response.location.endswith("/publicacion/3")
    with client.session_transaction() as sesion:
        assert not sesion.get("carrito")
    assert b"tu propia publicaci" in client.get("/publicacion/3").data


def test_otro_usuario_si_ve_el_boton_en_publicacion_ajena(client):
    ingresar(client)
    assert b"Agregar al carrito" in client.get("/publicacion/1").data


def salir(client):
    token = extraer_token(client.get("/cuenta/perfil"))
    response = client.post("/cuenta/salir", data={"csrf_token": token})
    assert response.status_code == 302


def ingresar_vendedor(client):
    response = client.get("/cuenta/ingresar")
    response = client.post("/cuenta/ingresar", data={
        "csrf_token": extraer_token(response),
        "email": "vendedor@example.com",
        "contrasena": "password-vendedor",
    })
    assert response.status_code == 302


def comprar(client, id_publicacion, cantidad):
    agregar(client, id_publicacion=id_publicacion, cantidad=cantidad)
    token = extraer_token(client.get("/carrito.html"))
    return client.post("/carrito/confirmar", data={"csrf_token": token})


def test_mis_compras_requiere_iniciar_sesion(client):
    response = client.get("/cuenta/compras")
    assert response.status_code == 302
    assert response.location.startswith("/cuenta/ingresar")


def test_compras_acumulan_monedas_sin_limite_de_saldo(client):
    ingresar(client)

    # Varias compras seguidas: nunca se rechaza por falta de monedas.
    assert comprar(client, 1, 2).status_code == 302   # 20.000
    assert comprar(client, 1, 3).status_code == 302   # 30.000
    assert comprar(client, 2, 2).status_code == 302   # 5.001

    assert Compra.query.count() == 3
    perfil = client.get("/cuenta/perfil")
    assert b"Monedas gastadas" in perfil.data
    assert "🪙 55.001".encode() in perfil.data


def test_vendedor_ve_sus_ventas_y_monedas_ganadas(client):
    ingresar(client)
    comprar(client, 1, 2)   # 20.000 para el vendedor (id 2)
    salir(client)

    ingresar_vendedor(client)
    response = client.get("/cuenta/compras")
    assert b"Mis ventas" in response.data
    assert b"Comprador: Compradora" in response.data
    assert "Monedas ganadas por ventas".encode() in response.data
    assert "🪙 20.000".encode() in response.data

    perfil = client.get("/cuenta/perfil")
    assert "🪙 20.000".encode() in perfil.data