"""Pruebas de búsqueda y categorías conectadas a la base de datos."""
import os
import tempfile
from decimal import Decimal

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
            Usuario(nombre="Ana Vendedora", email="ana@example.com",
                    contrasena=generate_password_hash("password-ana"), vendedor=True),
            Usuario(nombre="Beto Vendedor", email="beto@example.com",
                    contrasena=generate_password_hash("password-beto"), vendedor=True),
        ])
        db.session.commit()
        with app.test_client() as test_client:
            yield test_client

    try:
        os.remove(db_path)
    except OSError:
        pass


def publicar(nombre, categoria, id_usuario, precio="1000.00", stock=3,
             estado="activo", descripcion="Descripcion de prueba"):
    producto = Producto(nombre=nombre, categoria=categoria, descripcion=descripcion)
    db.session.add(producto)
    db.session.flush()
    publicacion = Publicacion(
        producto=producto, id_usuario=id_usuario, stock=stock,
        precio=Decimal(precio), estado=estado, condicion="Nuevo",
    )
    db.session.add(publicacion)
    db.session.commit()
    return publicacion


def html(client, url):
    respuesta = client.get(url)
    assert respuesta.status_code == 200
    return respuesta.data.decode()


def test_busqueda_muestra_publicaciones_de_distintos_vendedores(client):
    publicar("Consola Retro de Ana", "consolas", 1)
    publicar("Consola Retro de Beto", "consolas", 2)

    pagina = html(client, "/busqueda.html?q=retro")
    assert "Consola Retro de Ana" in pagina
    assert "Consola Retro de Beto" in pagina
    assert "2 productos encontrados" in pagina
    assert "Vendedor: Ana Vendedora" in pagina


def test_busqueda_ignora_tildes_y_mayusculas(client):
    publicar("Teclado mec\u00e1nico RGB", "perifericos", 1)
    assert "Teclado mec\u00e1nico RGB" in html(client, "/busqueda.html?q=MECANICO")


def test_busqueda_encuentra_por_categoria(client):
    publicar("Maquina arcade", "consolas", 1)
    publicar("Auriculares", "audio", 2)

    pagina = html(client, "/busqueda.html?q=consolas")
    assert "Maquina arcade" in pagina
    assert "Auriculares" not in pagina


def test_busqueda_exige_todas_las_palabras(client):
    publicar("Mouse gamer RGB", "accesorios", 1)
    publicar("Mouse inalambrico", "accesorios", 2)

    pagina = html(client, "/busqueda.html?q=mouse gamer")
    assert "Mouse gamer RGB" in pagina
    assert "Mouse inalambrico" not in pagina


def test_busqueda_no_muestra_pausadas_finalizadas_ni_sin_stock(client):
    publicar("Item pausado", "consolas", 1, estado="pausado")
    publicar("Item finalizado", "consolas", 1, estado="finalizado")
    publicar("Item agotado", "consolas", 1, stock=0)
    publicar("Item activo", "consolas", 1)

    pagina = html(client, "/busqueda.html?q=item")
    assert "Item activo" in pagina
    assert "Item pausado" not in pagina
    assert "Item finalizado" not in pagina
    assert "Item agotado" not in pagina


def test_busqueda_sin_resultados_y_sin_consulta(client):
    assert "No encontramos resultados" in html(client, "/busqueda.html?q=zzzz")
    publicar("Cualquier cosa", "pc", 1)
    pagina = html(client, "/busqueda.html")
    assert "Todos los productos" in pagina
    assert "Cualquier cosa" in pagina


def test_busqueda_escapa_html_del_nombre(client):
    publicar("<script>alert(1)</script>", "pc", 1)
    pagina = html(client, "/busqueda.html")
    assert "<script>alert(1)</script>" not in pagina
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in pagina


def test_busqueda_enlaza_al_detalle_real(client):
    publicacion = publicar("Producto enlazado", "pc", 1)
    pagina = html(client, "/busqueda.html?q=enlazado")
    assert f'href="/publicacion/{publicacion.id_publicacion}"' in pagina


def test_busqueda_ordena_por_precio_y_nombre(client):
    publicar("Zeta1", "pc", 1, precio="3000.00")
    publicar("Alfa1", "pc", 1, precio="1000.00")
    publicar("Medio1", "pc", 2, precio="2000.00")

    menor = html(client, "/busqueda.html?orden=menor")
    assert menor.index("Alfa1") < menor.index("Medio1") < menor.index("Zeta1")
    mayor = html(client, "/busqueda.html?orden=mayor")
    assert mayor.index("Zeta1") < mayor.index("Medio1") < mayor.index("Alfa1")
    nombre = html(client, "/busqueda.html?orden=nombre")
    assert nombre.index("Alfa1") < nombre.index("Medio1") < nombre.index("Zeta1")
    # Un orden inv\u00e1lido no rompe la p\u00e1gina.
    assert client.get("/busqueda.html?orden=hack").status_code == 200


def test_busqueda_pagina_los_resultados(client):
    for numero in range(30):
        publicar(f"Producto numerado {numero}", "pc", 1)

    primera = html(client, "/busqueda.html")
    assert primera.count('class="product-card"') == 24
    assert "P\u00e1gina 1 de 2" in primera

    segunda = html(client, "/busqueda.html?pagina=2")
    assert segunda.count('class="product-card"') == 6

    # Una p\u00e1gina fuera de rango o inv\u00e1lida se corrige sola.
    assert html(client, "/busqueda.html?pagina=99").count('class="product-card"') == 6
    assert html(client, "/busqueda.html?pagina=abc").count('class="product-card"') == 24


def test_categoria_lista_productos_propios_y_ajenos(client):
    publicar("Consola de Ana", "consolas", 1)
    publicar("Consola de Beto", "consolas", 2)
    publicar("Auriculares de Ana", "audio", 1)

    pagina = html(client, "/tal_categoria.html?categoria=consolas")
    assert "Consola de Ana" in pagina
    assert "Consola de Beto" in pagina
    assert "Auriculares de Ana" not in pagina
    assert "2 productos encontrados" in pagina

    audio = html(client, "/tal_categoria.html?categoria=audio")
    assert "Auriculares de Ana" in audio
    assert "Consola de Ana" not in audio


def test_categoria_invalida_vuelve_a_consolas(client):
    publicar("Consola cualquiera", "consolas", 1)
    pagina = html(client, "/tal_categoria.html?categoria=inexistente")
    assert "Consola cualquiera" in pagina


def test_categoria_oculta_publicaciones_no_activas(client):
    publicar("Pausada", "consolas", 1, estado="pausado")
    publicar("Visible", "consolas", 1)
    pagina = html(client, "/tal_categoria.html?categoria=consolas")
    assert "Visible" in pagina
    assert "Pausada" not in pagina


def test_categoria_sin_productos_muestra_aviso(client):
    pagina = html(client, "/tal_categoria.html?categoria=accesorios")
    assert "Todav\u00eda no hay productos en esta categor\u00eda" in pagina


def test_listado_de_categorias_cuenta_y_enlaza(client):
    publicar("Consola A", "consolas", 1)
    publicar("Consola B", "consolas", 2)
    publicar("Consola pausada", "consolas", 1, estado="pausado")
    publicar("Auriculares", "audio", 1)

    pagina = html(client, "/categorias.html")
    assert "Ver consolas (2) \u2192" in pagina
    assert "Ver audio (1) \u2192" in pagina
    assert "Ver videojuegos (0) \u2192" in pagina
    assert 'href="tal_categoria.html?categoria=consolas"' in pagina