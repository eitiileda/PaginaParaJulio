const productos = [
            {
                id: 1,
                nombre: "Consola PlayStation 5",
                precio: 899999,
                categoria: "consolas",
                icono: "🎮",
                estado: "Nuevo"
            },
            {
                id: 2,
                nombre: "Control inalámbrico para consola",
                precio: 89999,
                categoria: "consolas",
                icono: "🕹️",
                estado: "Nuevo"
            },
            {
                id: 3,
                nombre: "Consola Xbox Series S",
                precio: 649999,
                categoria: "consolas",
                icono: "🎮",
                estado: "Usado"
            },
            {
                id: 4,
                nombre: "Auriculares gamer con micrófono",
                precio: 54999,
                categoria: "audio",
                icono: "🎧",
                estado: "Nuevo"
            },
            {
                id: 5,
                nombre: "Micrófono para streaming",
                precio: 72999,
                categoria: "audio",
                icono: "🎙️",
                estado: "Usado"
            },
            {
                id: 6,
                nombre: "Teclado mecánico RGB",
                precio: 72500,
                categoria: "perifericos",
                icono: "⌨️",
                estado: "Nuevo"
            },
            {
                id: 7,
                nombre: "Mouse gamer RGB",
                precio: 32999,
                categoria: "perifericos",
                icono: "🖱️",
                estado: "Nuevo"
            },
            {
                id: 8,
                nombre: "Monitor gamer",
                precio: 299999,
                categoria: "perifericos",
                icono: "🖥️",
                estado: "Usado"
            },
            {
                id: 9,
                nombre: "Placa de video para PC",
                precio: 499999,
                categoria: "componentes",
                icono: "⚙️",
                estado: "Nuevo"
            },
            {
                id: 10,
                nombre: "Computadora gamer armada",
                precio: 1099999,
                categoria: "pc",
                icono: "🖥️",
                estado: "Nuevo"
            },
            {
                id: 11,
                nombre: "Videojuego de aventura",
                precio: 59999,
                categoria: "videojuegos",
                icono: "🎮",
                estado: "Usado"
            },
            {
                id: 12,
                nombre: "Cable HDMI",
                precio: 8999,
                categoria: "accesorios",
                icono: "🔌",
                estado: "Nuevo"
            }
        ];

        const nombresCategorias = {
            consolas: "Consolas",
            videojuegos: "Videojuegos",
            perifericos: "Periféricos gamer",
            componentes: "Componentes de PC",
            pc: "PC Gamer",
            audio: "Audio gamer",
            accesorios: "Accesorios"
        };

        const descripcionesCategorias = {
            consolas: "Descubrí consolas y controles para disfrutar tus juegos favoritos.",
            videojuegos: "Encontrá videojuegos de distintos géneros para ampliar tu colección.",
            perifericos: "Mejorá tu experiencia con teclados, mouse y monitores gamer.",
            componentes: "Explorá componentes para armar o actualizar tu computadora.",
            pc: "Descubrí computadoras gamer para jugar y crear contenido.",
            audio: "Encontrá auriculares y micrófonos para jugar y hacer streaming.",
            accesorios: "Completá tu equipo con cables y accesorios para gaming."
        };

        const parametros = new URLSearchParams(window.location.search);

        // Acepta tanto ?categoria=consolas como ?q=consolas.
        const categoriaSolicitada = (
            parametros.get("categoria") ||
            parametros.get("q") ||
            "consolas"
        ).toLowerCase();

        const categoriaActual =
            nombresCategorias[categoriaSolicitada] ? categoriaSolicitada : "consolas";

        document.getElementById("tituloCategoria").textContent =
            nombresCategorias[categoriaActual];

        document.getElementById("migaCategoria").textContent =
            nombresCategorias[categoriaActual];

        document.getElementById("descripcionCategoria").textContent =
            descripcionesCategorias[categoriaActual];

        document.getElementById("subtituloProductos").textContent =
            "Productos de " + nombresCategorias[categoriaActual];

        document.querySelectorAll("#selectorCategorias a").forEach(enlace => {
            const url = new URL(enlace.href);
            if (url.searchParams.get("categoria") === categoriaActual) {
                enlace.classList.add("activa");
            }
        });

        function formatoPrecio(precio) {
            return new Intl.NumberFormat("es-AR", {
                style: "currency",
                currency: "ARS",
                maximumFractionDigits: 0
            }).format(precio);
        }

        function mostrarProductos() {
            const orden = document.getElementById("orden").value;
            const contenedor = document.getElementById("listaProductos");

            let filtrados = productos.filter(producto =>
                producto.categoria === categoriaActual
            );

            if (orden === "menor") {
                filtrados.sort((a, b) => a.precio - b.precio);
            } else if (orden === "mayor") {
                filtrados.sort((a, b) => b.precio - a.precio);
            } else if (orden === "nombre") {
                filtrados.sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
            }

            document.getElementById("cantidad").textContent =
                filtrados.length + (filtrados.length === 1
                    ? " producto encontrado"
                    : " productos encontrados");

            if (filtrados.length === 0) {
                contenedor.innerHTML = `
                    <div class="sin-resultados">
                        <h3>Próximamente habrá productos en esta categoría</h3>
                        <p>Mientras tanto, podés explorar otras categorías.</p>
                        <a href="categorias.html">Ver todas las categorías</a>
                    </div>
                `;
                return;
            }

            contenedor.innerHTML = filtrados.map(producto => `
                <article class="producto">
                    <div class="imagen-producto">${producto.icono}</div>

                    <div class="info-producto">
                        <span class="estado">${producto.estado}</span>
                        <h3 class="nombre">${producto.nombre}</h3>
                        <p class="precio">${formatoPrecio(producto.precio)}</p>
                        <p class="cuotas">Consultá las opciones de pago</p>

                        <a
                            class="ver-producto"
                            href="producto.html?id=${producto.id}"
                        >
                            Ver producto
                        </a>
                    </div>
                </article>
            `).join("");
        }

        document.getElementById("orden").addEventListener("change", mostrarProductos);

        mostrarProductos();
