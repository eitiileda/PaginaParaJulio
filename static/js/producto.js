/*
          Catálogo de demostración.
          Los identificadores coinciden con algunos productos
          de las páginas de búsqueda y categorías.
        */

        const productos = [
            {
                id: 1,
                nombre: "Consola PlayStation 5",
                precio: 899999,
                estado: "Nuevo",
                categoria: "Consolas",
                icono: "🎮",
                disponible: true,
                descripcion:
                    "Consola de videojuegos para disfrutar de títulos " +
                    "de última generación. Verificá los accesorios " +
                    "incluidos y las condiciones de la publicación.",
                caracteristicas: {
                    "Categoría": "Consolas",
                    "Marca": "PlayStation",
                    "Estado": "Nuevo",
                    "Conectividad": "HDMI y conexión inalámbrica"
                }
            },
            {
                id: 2,
                nombre: "Control inalámbrico",
                precio: 89999,
                estado: "Nuevo",
                categoria: "Consolas",
                icono: "🕹️",
                disponible: true,
                descripcion:
                    "Control para videojuegos. Revisá la compatibilidad " +
                    "con tu consola antes de realizar la compra.",
                caracteristicas: {
                    "Categoría": "Accesorios",
                    "Conectividad": "Inalámbrica",
                    "Estado": "Nuevo"
                }
            },
            {
                id: 3,
                nombre: "Consola Xbox Series S",
                precio: 649999,
                estado: "Usado",
                categoria: "Consolas",
                icono: "🎮",
                disponible: true,
                descripcion:
                    "Consola usada para videojuegos. Consultá con el " +
                    "vendedor el estado, los accesorios incluidos y la garantía.",
                caracteristicas: {
                    "Categoría": "Consolas",
                    "Marca": "Xbox",
                    "Estado": "Usado"
                }
            },
            {
                id: 4,
                nombre: "Auriculares gamer con micrófono",
                precio: 54999,
                estado: "Nuevo",
                categoria: "Audio gamer",
                icono: "🎧",
                disponible: true,
                descripcion:
                    "Auriculares para jugar y comunicarse con otros " +
                    "jugadores. Consultá la compatibilidad con tu dispositivo.",
                caracteristicas: {
                    "Categoría": "Audio gamer",
                    "Conectividad": "Consultar publicación",
                    "Estado": "Nuevo"
                }
            },
            {
                id: 5,
                nombre: "Micrófono para streaming",
                precio: 72999,
                estado: "Usado",
                categoria: "Audio gamer",
                icono: "🎙️",
                disponible: true,
                descripcion:
                    "Micrófono para grabación, comunicación y streaming. " +
                    "Verificá sus conexiones y accesorios incluidos.",
                caracteristicas: {
                    "Categoría": "Audio gamer",
                    "Estado": "Usado"
                }
            },
            {
                id: 6,
                nombre: "Teclado mecánico RGB",
                precio: 72500,
                estado: "Nuevo",
                categoria: "Periféricos",
                icono: "⌨️",
                disponible: true,
                descripcion:
                    "Teclado para videojuegos y uso cotidiano con " +
                    "iluminación RGB. Consultá la distribución de teclas.",
                caracteristicas: {
                    "Categoría": "Periféricos",
                    "Iluminación": "RGB",
                    "Estado": "Nuevo"
                }
            },
            {
                id: 7,
                nombre: "Mouse gamer RGB",
                precio: 32999,
                estado: "Nuevo",
                categoria: "Periféricos",
                icono: "🖱️",
                disponible: true,
                descripcion:
                    "Mouse gamer para PC con iluminación RGB. " +
                    "Consultá sus especificaciones antes de comprar.",
                caracteristicas: {
                    "Categoría": "Periféricos",
                    "Iluminación": "RGB",
                    "Estado": "Nuevo"
                }
            },
            {
                id: 8,
                nombre: "Monitor gamer",
                precio: 299999,
                estado: "Usado",
                categoria: "Periféricos",
                icono: "🖥️",
                disponible: true,
                descripcion:
                    "Monitor usado para jugar y trabajar. Consultá " +
                    "resolución, frecuencia y estado con el vendedor.",
                caracteristicas: {
                    "Categoría": "Periféricos",
                    "Estado": "Usado"
                }
            },
            {
                id: 9,
                nombre: "Placa de video para PC",
                precio: 499999,
                estado: "Nuevo",
                categoria: "Componentes",
                icono: "⚙️",
                disponible: true,
                descripcion:
                    "Componente para mejorar el rendimiento gráfico " +
                    "de una computadora. Verificá compatibilidad y modelo.",
                caracteristicas: {
                    "Categoría": "Componentes",
                    "Estado": "Nuevo"
                }
            },
            {
                id: 10,
                nombre: "Computadora gamer armada",
                precio: 1099999,
                estado: "Nuevo",
                categoria: "Computadoras gamer",
                icono: "🖥️",
                disponible: true,
                descripcion:
                    "Computadora de demostración para gaming. " +
                    "Consultá procesador, memoria, almacenamiento y placa de video.",
                caracteristicas: {
                    "Categoría": "Computadoras gamer",
                    "Estado": "Nuevo"
                }
            },
            {
                id: 11,
                nombre: "Videojuego de aventura",
                precio: 59999,
                estado: "Usado",
                categoria: "Videojuegos",
                icono: "🎮",
                disponible: true,
                descripcion:
                    "Videojuego usado. Consultá la plataforma, " +
                    "el idioma y el estado del producto antes de comprar.",
                caracteristicas: {
                    "Categoría": "Videojuegos",
                    "Estado": "Usado"
                }
            },
            {
                id: 12,
                nombre: "Cable HDMI",
                precio: 8999,
                estado: "Nuevo",
                categoria: "Accesorios",
                icono: "🔌",
                disponible: true,
                descripcion:
                    "Cable HDMI para conectar dispositivos compatibles. " +
                    "Verificá la longitud y las especificaciones necesarias.",
                caracteristicas: {
                    "Categoría": "Accesorios",
                    "Estado": "Nuevo"
                }
            }
        ];

        const parametros = new URLSearchParams(
            window.location.search
        );

        const idProducto = Number(parametros.get("id") || 1);

        const producto = productos.find(
            elemento => elemento.id === idProducto
        ) || productos[0];

        const formatoPrecio = precio =>
            new Intl.NumberFormat("es-AR", {
                style: "currency",
                currency: "ARS",
                maximumFractionDigits: 0
            }).format(precio);

        // Actualizar información del producto

        document.title = producto.nombre + " | GameMarket";

        document.getElementById("breadcrumb-name").textContent =
            producto.nombre;

        document.getElementById("product-name").textContent =
            producto.nombre;

        document.getElementById("product-price").textContent =
            formatoPrecio(producto.precio);

        document.getElementById("product-condition").textContent =
            producto.estado;

        document.getElementById("product-image").textContent =
            producto.icono;

        document.getElementById("product-image").setAttribute(
            "aria-label",
            producto.nombre
        );

        document.getElementById("product-meta").textContent =
            "Código de producto: GM-" +
            String(producto.id).padStart(3, "0");

        document.getElementById("product-stock").textContent =
            producto.disponible ? "Disponible" : "Sin stock";

        document.getElementById("product-stock").style.color =
            producto.disponible ? "#16834a" : "#b42318";

        document.getElementById("product-description").textContent =
            producto.descripcion;

        // Crear tabla de características

        const tabla = document.getElementById(
            "product-specifications"
        );

        tabla.innerHTML = "";

        const caracteristicas = {
            "Categoría": producto.categoria,
            ...producto.caracteristicas
        };

        Object.entries(caracteristicas).forEach(([nombre, valor]) => {
            const fila = document.createElement("tr");

            const celdaNombre = document.createElement("td");
            const celdaValor = document.createElement("td");

            celdaNombre.textContent = nombre;
            celdaValor.textContent = valor;

            fila.append(celdaNombre, celdaValor);
            tabla.appendChild(fila);
        });

        // Mensajes de interacción

        const aviso = document.getElementById("notice");

        function mostrarAviso(mensaje) {
            aviso.textContent = mensaje;
            aviso.classList.add("visible");
        }

        const cantidadInput = document.getElementById("quantity");

        function obtenerCantidad() {
            const cantidad = Number(cantidadInput.value);

            if (
                !Number.isInteger(cantidad) ||
                cantidad < 1 ||
                cantidad > 10
            ) {
                mostrarAviso(
                    "Ingresá una cantidad entera entre 1 y 10."
                );
                return null;
            }

            if (!producto.disponible) {
                mostrarAviso("Este producto no está disponible.");
                return null;
            }

            return cantidad;
        }

        // Agregar al carrito usando localStorage

        document.getElementById("cart-button").addEventListener(
            "click",
            function() {
                const cantidad = obtenerCantidad();

                if (cantidad === null) return;

                let carrito = [];

                try {
                    carrito = JSON.parse(
                        localStorage.getItem("gamemarket_carrito") || "[]"
                    );

                    if (!Array.isArray(carrito)) carrito = [];
                } catch {
                    carrito = [];
                }

                const existente = carrito.find(
                    item => item.id === producto.id
                );

                if (existente) {
                    existente.cantidad += cantidad;
                } else {
                    carrito.push({
                        id: producto.id,
                        nombre: producto.nombre,
                        precio: producto.precio,
                        icono: producto.icono,
                        cantidad: cantidad
                    });
                }

                localStorage.setItem(
                    "gamemarket_carrito",
                    JSON.stringify(carrito)
                );

                mostrarAviso(
                    "¡Producto agregado al carrito! Cantidad: " +
                    cantidad + "."
                );
            }
        );

        // Comprar ahora: preparar el producto en el carrito
        // y dirigir al usuario a la página del carrito.

        document.getElementById("buy-button").addEventListener(
            "click",
            function() {
                const cantidad = obtenerCantidad();

                if (cantidad === null) return;

                let carrito = [];

                try {
                    carrito = JSON.parse(
                        localStorage.getItem("gamemarket_carrito") || "[]"
                    );

                    if (!Array.isArray(carrito)) carrito = [];
                } catch {
                    carrito = [];
                }

                const existente = carrito.find(
                    item => item.id === producto.id
                );

                if (existente) {
                    existente.cantidad += cantidad;
                } else {
                    carrito.push({
                        id: producto.id,
                        nombre: producto.nombre,
                        precio: producto.precio,
                        icono: producto.icono,
                        cantidad: cantidad
                    });
                }

                localStorage.setItem(
                    "gamemarket_carrito",
                    JSON.stringify(carrito)
                );

                window.location.href = "carrito.html";
            }
        );
