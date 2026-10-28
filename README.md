# GameMarket — versión preliminar modular

Proyecto académico de compraventa de videojuegos, consolas y accesorios. Esta versión ordena el código para poder agregar módulos sin rehacer todo el proyecto.

## Estructura

```text
GameMarket_preliminar/
├── app.py                    # Punto de entrada de Flask
├── config.py                 # Configuración por variables de entorno
├── gamemarket/
│   ├── __init__.py           # Factory de la aplicación
│   ├── extensions.py         # Extensiones compartidas
│   ├── models.py             # Modelos de SQLAlchemy
│   └── routes.py             # Rutas HTTP
├── templates/                # Una plantilla HTML por pantalla
├── static/
│   ├── css/                  # CSS separado por pantalla + base.css
│   └── js/                   # JavaScript separado por pantalla
├── database/
│   ├── schema.sql            # Esquema inicial recomendado
│   └── schema_demo_original.sql # Script anterior, conservado como referencia
├── requirements.txt
└── .env.example
```

## Cómo arrancar en Windows

1. Instalá Python 3.10 o superior.
2. Abrí una terminal dentro de esta carpeta.
3. Creá un entorno virtual e instalá dependencias:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. Opcional: copiá `.env.example` como `.env` y configurá `DATABASE_URL`.
5. Ejecutá:

   ```powershell
   py app.py
   ```

6. Abrí `http://127.0.0.1:5000`.

Para correr las pruebas de humo, ejecutá `pytest` desde la carpeta del proyecto.

Por defecto se usa SQLite local para que la maqueta pueda arrancar sin instalar MySQL. Para conectar MySQL, configurá `DATABASE_URL` en el entorno, por ejemplo:

```text
mysql+pymysql://USUARIO:CONTRASENA@localhost/tienda_online
```

Si la contraseña contiene caracteres especiales, deben codificarse para una URL. No publiques `.env` ni contraseñas.

## Estado de esta versión

- Las pantallas HTML existentes se conservan como plantillas.
- Los bloques CSS y JavaScript se separaron a `static/`; se conservó el helper anterior de historial como `static/js/historial-storage.js` para reutilizarlo más adelante.
- Las rutas de páginas tienen nombres consistentes y los enlaces Jinja más evidentes fueron corregidos.
- La carga de publicaciones tiene validación básica y rollback ante errores.
- Los modelos se agruparon en un módulo.
- La base local se crea al iniciar. Para una aplicación real conviene incorporar migraciones con Flask-Migrate/Alembic.
- Muchas pantallas siguen siendo prototipos visuales con productos ficticios y lógica en el navegador. Todavía no hay autenticación, autorización, pagos reales ni sincronización completa con MySQL.
- `database/schema_demo_original.sql` se conserva como referencia del archivo anterior. Sus usuarios/contraseñas y números de tarjeta de ejemplo son datos inseguros y no deben usarse en un entorno real. El esquema nuevo evita guardar números de tarjeta y recomienda guardar hashes de contraseña.

## Próximos módulos sugeridos

1. Autenticación y sesiones.
2. CRUD de productos y publicaciones.
3. Búsqueda y filtros conectados a la base de datos.
4. Carrito y órdenes.
5. Perfil de vendedor y reputación.
6. Mensajes entre usuarios.
7. Pruebas automatizadas y migraciones de base de datos.

## Convención de trabajo

- HTML/Jinja: `templates/`.
- Estilos: `static/css/`.
- JavaScript del navegador: `static/js/`.
- Modelos y lógica de datos: `gamemarket/models.py` y futuros módulos de servicios.
- Rutas: `gamemarket/routes.py`; si crece, dividirlas en Blueprints por módulo.
