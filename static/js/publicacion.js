const formulario = document.getElementById("formulario-publicacion");

        const campoNombre = document.getElementById("nombre");
        const campoCategoria = document.getElementById("categoria");
        const campoEstado = document.getElementById("estado");
        const campoPrecio = document.getElementById("precio");
        const campoStock = document.getElementById("stock");
        const campoDescripcion = document.getElementById("descripcion");
        const campoImagen = document.getElementById("imagen");

        const mensaje = document.getElementById("mensaje");
        const vistaImagen = document.getElementById("vista-imagen");
        const imagenPrevia = document.getElementById("imagen-previa");

        let urlImagen = null;

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

        function formatoPrecio(valor) {
            const numero = Number(valor) || 0;

            return numero.toLocaleString("es-AR", {
                style: "currency",
                currency: "ARS",
                maximumFractionDigits: 0
            });
        }

        function actualizarVistaPrevia() {
            document.getElementById("nombre-previa").textContent =
                campoNombre.value.trim() || "Nombre del producto";

            const opcionCategoria =
                campoCategoria.options[campoCategoria.selectedIndex];

            document.getElementById("categoria-previa").textContent =
                campoCategoria.value
                    ? opcionCategoria.text.toUpperCase()
                    : "CATEGORÍA";

            document.getElementById("estado-previa").textContent =
                campoEstado.value || "Estado del producto";

            document.getElementById("precio-previa").textContent =
                formatoPrecio(campoPrecio.value);

            document.getElementById("stock-previa").textContent =
                "Unidades disponibles: " + (campoStock.value || "1");

            document.getElementById("descripcion-previa").textContent =
                campoDescripcion.value.trim() ||
                "La descripción de tu producto aparecerá acá.";
        }

        [
            campoNombre,
            campoCategoria,
            campoEstado,
            campoPrecio,
            campoStock,
            campoDescripcion
        ].forEach(campo => {
            campo.addEventListener("input", actualizarVistaPrevia);
            campo.addEventListener("change", actualizarVistaPrevia);
        });

        campoImagen.addEventListener("change", function() {
            const archivo = campoImagen.files[0];

            if (urlImagen) {
                URL.revokeObjectURL(urlImagen);
                urlImagen = null;
            }

            if (!archivo) {
                vistaImagen.style.display = "none";
                imagenPrevia.textContent = "🎮";
                return;
            }

            const tiposPermitidos = [
                "image/jpeg",
                "image/png",
                "image/webp"
            ];

            if (!tiposPermitidos.includes(archivo.type)) {
                campoImagen.value = "";
                vistaImagen.style.display = "none";
                imagenPrevia.textContent = "🎮";
                alert("Seleccioná una imagen JPG, PNG o WEBP.");
                return;
            }

            if (archivo.size > 5 * 1024 * 1024) {
                campoImagen.value = "";
                vistaImagen.style.display = "none";
                imagenPrevia.textContent = "🎮";
                alert("La imagen no puede superar los 5 MB.");
                return;
            }

            urlImagen = URL.createObjectURL(archivo);

            vistaImagen.src = urlImagen;
            vistaImagen.style.display = "block";

            imagenPrevia.innerHTML = "";
            const imagen = document.createElement("img");
            imagen.src = urlImagen;
            imagen.alt = "Vista previa del producto";
            imagenPrevia.appendChild(imagen);
        });

        formulario.addEventListener("submit", function(evento) {
            evento.preventDefault();

            const nombre = campoNombre.value.trim();
            const precio = Number(campoPrecio.value);
            const stock = Number(campoStock.value);
            const descripcion = campoDescripcion.value.trim();

            if (!nombre || !campoCategoria.value ||
                !campoEstado.value || !descripcion) {
                mostrarMensaje(
                    "Completá todos los campos obligatorios.",
                    "error"
                );
                return;
            }

            if (!Number.isInteger(precio) || precio <= 0 ||
                precio > 999999999) {
                mostrarMensaje(
                    "Ingresá un precio entero válido y mayor que cero.",
                    "error"
                );
                return;
            }

            if (!Number.isInteger(stock) || stock < 1 || stock > 9999) {
                mostrarMensaje(
                    "Ingresá una cantidad válida entre 1 y 9999.",
                    "error"
                );
                return;
            }

            mostrarMensaje(
                "¡Formulario validado! La vista previa está lista. " +
                "Para publicar y guardar productos de verdad, " +
                "necesitamos conectar esta página con una base de datos.",
                "exito"
            );
        });

        function mostrarMensaje(texto, tipo) {
            mensaje.textContent = texto;
            mensaje.className = "mensaje " + tipo;
        }

        formulario.addEventListener("reset", function() {
            setTimeout(function() {
                if (urlImagen) {
                    URL.revokeObjectURL(urlImagen);
                    urlImagen = null;
                }

                vistaImagen.removeAttribute("src");
                vistaImagen.style.display = "none";
                imagenPrevia.textContent = "🎮";

                mensaje.textContent = "";
                mensaje.className = "mensaje";

                actualizarVistaPrevia();
            }, 0);
        });

        actualizarVistaPrevia();
