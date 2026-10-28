// Productos ficticios para probar la búsqueda.
        // Luego se podrán obtener desde el backend o una base de datos.

        const productos = [
            {
                id: 1,
                nombre: "Consola PlayStation 5",
                categoria: "consolas",
                precio: 899999,
                estado: "Nuevo",
                icono: "🎮",
                disponible: true
            },
            {
                id: 2,
                nombre: "Control inalámbrico para consola",
                categoria: "consolas",
                precio: 89999,
                estado: "Nuevo",
                icono: "🕹️",
                disponible: true
            },
            {
                id: 3,
                nombre: "Consola Xbox Series S",
                categoria: "consolas",
                precio: 649999,
                estado: "Usado",
                icono: "🎮",
                disponible: true
            },
            {
                id: 4,
                nombre: "Auriculares gamer con micrófono",
                categoria: "audio",
                precio: 54999,
                estado: "Nuevo",
                icono: "🎧",
                disponible: true
            },
            {
                id: 5,
                nombre: "Micrófono para streaming",
                categoria: "audio",
                precio: 72999,
                estado: "Usado",
                icono: "🎙️",
                disponible: true
            },
            {
                id: 6,
                nombre: "Teclado mecánico RGB",
                categoria: "perifericos",
                precio: 72500,
                estado: "Nuevo",
                icono: "⌨️",
                disponible: true
            },
            {
                id: 7,
                nombre: "Mouse gamer RGB",
                categoria: "perifericos",
                precio: 32999,
                estado: "Nuevo",
                icono: "🖱️",
                disponible: true
            },
            {
                id: 8,
                nombre: "Monitor gamer",
                categoria: "perifericos",
                precio: 299999,
                estado: "Usado",
                icono: "🖥️",
                disponible: true
            },
            {
                id: 9,
                nombre: "Placa de video para PC",
                categoria: "componentes",
                precio: 499999,
                estado: "Nuevo",
                icono: "⚙️",
                disponible: true
            },
            {
                id: 10,
                nombre: "Computadora gamer armada",
                categoria: "pc",
                precio: 1099999,
                estado: "Nuevo",
                icono: "🖥️",
                disponible: true
            },
            {
                id: 11,
                nombre: "Videojuego de aventura",
                categoria: "videojuegos",
                precio: 59999,
                estado: "Usado",
                icono: "🎮",
                disponible: true
            },
            {
                id: 12,
                nombre: "Cable HDMI",
                categoria: "accesorios",
                precio: 8999,
                estado: "Nuevo",
                icono: "🔌",
                disponible: true
            }
        ];

        const parametros = new URLSearchParams(
            window.location.search
        );

        const consultaInicial = parametros.get("q") || "";

        const campoBusqueda =
            document.getElementById("search-input");

        const titulo =
            document.getElementById("page-title");

        const descripcion =
            document.getElementById("page-description");

        const contador =
            document.getElementById("results-count");

        const grid =
            document.getElementById("products-grid");

        const selectorOrden =
            document.getElementById("sort-select");

        campoBusqueda.value = consultaInicial;

        function normalizar(texto) {
            return texto
                .toLocaleLowerCase("es")
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "")
                .trim();
        }

        function formatoPrecio(precio) {
            return new Intl.NumberFormat("es-AR", {
                style: "currency",
                currency: "ARS",
                maximumFractionDigits: 0
            }).format(precio);
        }

        function mostrarResultados() {
            const consulta = normalizar(campoBusqueda.value);

            titulo.textContent = consulta
                ? 'Resultados para "' + campoBusqueda.value.trim() + '"'
                : "Todos los productos";

            descripcion.textContent = consulta
                ? "Estos son los productos que coinciden con tu búsqueda."
                : "Explorá nuestro catálogo de productos gamer.";

            let resultados = productos.filter(producto => {
                const textoProducto = normalizar(
                    producto.nombre + " " + producto.categoria
                );

                return !consulta || textoProducto.includes(consulta);
            });

            const orden = selectorOrden.value;

            if (orden === "menor") {
                resultados.sort((a, b) => a.precio - b.precio);
            } else if (orden === "mayor") {
                resultados.sort((a, b) => b.precio - a.precio);
            } else if (orden === "nombre") {
                resultados.sort((a, b) =>
                    a.nombre.localeCompare(b.nombre, "es")
                );
            }

            contador.textContent =
                resultados.length +
                (resultados.length === 1
                    ? " producto encontrado"
                    : " productos encontrados");

            grid.innerHTML = "";

            if (resultados.length === 0) {
                grid.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">🔎</div>

                        <h2>No encontramos resultados</h2>

                        <p>
                            Probá con otras palabras o explorá
                            nuestras categorías para descubrir productos.
                        </p>

                        <a href="categorias.html" class="back-button">
                            Ver categorías
                        </a>
                    </div>
                `;

                return;
            }

            resultados.forEach(producto => {
                const tarjeta = document.createElement("article");
                tarjeta.className = "product-card";

                tarjeta.innerHTML = `
                    <div class="product-image" aria-hidden="true">
                        ${producto.icono}
                    </div>

                    <div class="product-info">
                        <span class="condition">
                            ${producto.estado}
                        </span>

                        <h2>${producto.nombre}</h2>

                        <p class="price">
                            ${formatoPrecio(producto.precio)}
                        </p>

                        <p class="installments">
                            Consultá las opciones de pago
                        </p>

                        <p class="availability ${
                            producto.disponible ? "" : "unavailable"
                        }">
                            ${
                                producto.disponible
                                    ? "Disponible"
                                    : "Sin stock"
                            }
                        </p>

                        <a
                            href="producto.html?id=${producto.id}"
                            class="product-button"
                        >
                            Ver producto
                        </a>
                    </div>
                `;

                grid.appendChild(tarjeta);
            });
        }

        selectorOrden.addEventListener(
            "change",
            mostrarResultados
        );

        mostrarResultados();
