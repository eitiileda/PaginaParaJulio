-- Ejecutar UNA sola vez (MySQL).
-- Los datos de demostración se cargaron sin categoría (productos.categoria = NULL),
-- por eso no aparecían en las páginas de categorías. Todos los productos demo
-- son videojuegos (sus imágenes se llaman cover_XXXX.jpg).
USE tienda_online;

UPDATE productos
SET categoria = 'videojuegos'
WHERE categoria IS NULL AND logo LIKE 'cover_%';