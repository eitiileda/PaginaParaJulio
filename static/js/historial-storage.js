// Registrar el producto en el historial
function registrarVisita(producto) {
    const clave = "gamemarket_historial";

    let historial = [];

    try {
        historial = JSON.parse(localStorage.getItem(clave) || "[]");

        if (!Array.isArray(historial)) {
            historial = [];
        }
    } catch (error) {
        historial = [];
    }

    // Evitar que el mismo producto aparezca repetido
    historial = historial.filter(
        item => Number(item.id) !== Number(producto.id)
    );

    historial.unshift({
        id: producto.id,
        nombre: producto.nombre,
        precio: producto.precio,
        icono: producto.icono,
        categoria: producto.categoria || "Gaming",
        fecha: new Date().toISOString()
    });

    // Guardar como máximo 30 productos
    historial = historial.slice(0, 30);

    localStorage.setItem(clave, JSON.stringify(historial));
}
