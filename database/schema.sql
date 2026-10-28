-- Esquema preliminar de GameMarket (MySQL 8+)
CREATE DATABASE IF NOT EXISTS tienda_online
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tienda_online;

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL COMMENT 'Guardar hash seguro, nunca la contraseña en texto plano',
    vendedor BOOLEAN NOT NULL DEFAULT TRUE,
    admin BOOLEAN NOT NULL DEFAULT FALSE,
    descripcion VARCHAR(255),
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    logo VARCHAR(255) DEFAULT 'default_avatar.png'
);

CREATE TABLE IF NOT EXISTS productos (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    logo VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS publicaciones (
    id_publicacion INT AUTO_INCREMENT PRIMARY KEY,
    id_producto INT NOT NULL,
    id_usuario INT NOT NULL,
    stock INT NOT NULL DEFAULT 1,
    precio DECIMAL(10,2) NOT NULL,
    estado ENUM('activo', 'pausado', 'finalizado') NOT NULL DEFAULT 'activo',
    descripcion_vendedor VARCHAR(255),
    valoracion DECIMAL(3,2) DEFAULT 5.00,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_publicaciones_producto FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto) ON DELETE CASCADE,
    CONSTRAINT fk_publicaciones_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    INDEX idx_publicaciones_estado_fecha (estado, fecha),
    INDEX idx_publicaciones_producto (id_producto),
    INDEX idx_publicaciones_usuario (id_usuario)
);

CREATE TABLE IF NOT EXISTS compras (
    id_compra INT AUTO_INCREMENT PRIMARY KEY,
    id_publicacion INT NOT NULL,
    id_comprador INT NOT NULL,
    cantidad INT NOT NULL DEFAULT 1,
    monto_total DECIMAL(10,2) NOT NULL,
    referencia_pago VARCHAR(255) NULL COMMENT 'Referencia/token del proveedor de pagos; no guardar datos de tarjeta',
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_compras_publicacion FOREIGN KEY (id_publicacion)
        REFERENCES publicaciones(id_publicacion),
    CONSTRAINT fk_compras_comprador FOREIGN KEY (id_comprador)
        REFERENCES usuarios(id_usuario),
    INDEX idx_compras_comprador_fecha (id_comprador, fecha)
);
