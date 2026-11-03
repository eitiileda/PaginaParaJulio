-- Ejecutar UNA sola vez sobre la base que ya tenés (MySQL).
-- db.create_all() crea tablas nuevas pero NO agrega columnas a tablas existentes.
USE tienda_online;

ALTER TABLE productos     ADD COLUMN categoria VARCHAR(50) NULL AFTER descripcion;
ALTER TABLE publicaciones ADD COLUMN condicion VARCHAR(20) NULL AFTER estado;
