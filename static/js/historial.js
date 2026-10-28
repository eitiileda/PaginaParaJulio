const CLAVE_HISTORIAL = "gamemarket_historial";

        const listaHistorial = document.getElementById("lista-historial");
        const seccionHistorial = document.getElementById("seccion-historial");
        const mensajeVacio = document.getElementById("mensaje-vacio");
        const botonLimpiar = document.getElementById("limpiar-historial");

        function escaparHTML(texto) {
            return String(texto ?? "").replace(/[&<>"']/g, caracter => {
                const entidades = {
                    "&": "&amp;",
                    "<": "&lt;",
                    ">": "&gt;",
                    '"': "&quot;",
                    "'": "&#39;"
                };

                return entidades[caracter];
            });
        }

        function obtenerHistorial() {
            try {
                const datos = JSON.parse(
                    localStorage.getItem(CLAVE_HISTORIAL) || "[]"
                );

                if (!Array.isArray(datos)) {
                    return [];
                }

                return datos.filter(producto =>
                    producto &&
                    Number.isFinite(Number(producto.id)) &&
                    producto.nombre &&
                    Number.isFinite(Number(producto.precio))
                );
            } catch (error) {
                return [];
            }
        }

        function formatoPrecio(precio) {
            return Number(precio).toLocaleString("es-AR", {
                style: "currency",
                currency: "ARS",
                maximumFractionDigits: 0
            });
        }

        function renderizarHistorial() {
            const historial = obtenerHistorial();

            if (historial.length === 0) {
                seccionHistorial.hidden = true;
                mensajeVacio.hidden = false;
                botonLimpiar.disabled = true;
                botonLimpiar.style.opacity = "0.5";
                return;
            }

            seccionHistorial.hidden = false;
            mensajeVacio.hidden = true;
            botonLimpiar.disabled = false;
            botonLimpiar.style.opacity = "1";

            listaHistorial.innerHTML = historial.map(producto => {
                const id = Number(producto.id);
                const nombre = escaparHTML(producto.nombre);
                const icono = escaparHTML(producto.icono || "🎮");
                const categoria = escaparHTML(producto.categoria || "Gaming");
                const precio = formatoPrecio(producto.precio);

                let fecha = "Visitado recientemente";

                if (producto.fecha) {
                    const fechaValida = new Date(producto.fecha);

                    if (!Number.isNaN(fechaValida.getTime())) {
                        fecha = "Visto el " + fechaValida.toLocaleDateString("es-AR");
                    }
                }

                return `
                    <article class="tarjeta">
                        <a href="producto.html?id=${encodeURIComponent(id)}"
                           aria-label="Ver ${nombre}">
                            <div class="producto-imagen">${icono}</div>
                        </a>

                        <div class="producto-contenido">
                            <p class="producto-categoria">${categoria}</p>
                            <h3 class="producto-nombre">${nombre}</h3>
                            <p class="producto-precio">${precio}</p>
                            <p class="producto-fecha">${escaparHTML(fecha)}</p>

                            <a
                                href="producto.html?id=${encodeURIComponent(id)}"
                                class="boton boton-principal"
                            >
                                Ver producto
                            </a>
                        </div>
                    </article>
                `;
            }).join("");
        }

        botonLimpiar.addEventListener("click", function() {
            const historial = obtenerHistorial();

            if (historial.length === 0) return;

            const confirmar = confirm(
                "¿Querés borrar todos los productos de tu historial?"
            );

            if (confirmar) {
                localStorage.removeItem(CLAVE_HISTORIAL);
                renderizarHistorial();
            }
        });

        renderizarHistorial();
