#-----------------------------------------------------------------#
# BASE DE DATOS OPTIMIZADA
#TIENDA ONLINE DE VIDEOJUEGOS #
#-----------------------------------------------------------------#
CREATE DATABASE IF NOT EXISTS tienda_online;
USE tienda_online;

#-----------------------------------------------------------------#
# USUARIOS #
#-----------------------------------------------------------------#

CREATE TABLE usuarios (
id_usuario INT AUTO_INCREMENT PRIMARY KEY,
nombre VARCHAR(100) NOT NULL,
email VARCHAR(150) NOT NULL UNIQUE,
contrasena VARCHAR(255) NOT NULL,
vendedor BOOL DEFAULT TRUE,
#Todos pueden comprar y vender
admin BOOL DEFAULT FALSE,
descripcion VARCHAR(255),
fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
logo VARCHAR(255) DEFAULT 'default_avatar.png'
);
#-----------------------------------------------------------------#
# PRODUCTOS #
#-----------------------------------------------------------------#
#Catálogo general de videojuegos
CREATE TABLE productos (
id_producto INT AUTO_INCREMENT PRIMARY KEY,
nombre VARCHAR(100) NOT NULL,
descripcion TEXT,
logo VARCHAR(255)
);

#-----------------------------------------------------------------#
# PUBLICACIONES #
#-----------------------------------------------------------------#
#Videojuegos puestos a la venta por los usuarios
CREATE TABLE publicaciones (
id_publicacion INT AUTO_INCREMENT PRIMARY KEY,
id_producto INT NOT NULL,
id_usuario INT NOT NULL,
#Usuario vendedor
stock INT NOT NULL DEFAULT 1,
precio DECIMAL(10,2) NOT NULL,
estado ENUM('activo', 'pausado', 'finalizado') DEFAULT 'activo',
descripcion_vendedor VARCHAR(255),
#Ej: "Código digital global" o "Disco impecable con caja"
valoracion DECIMAL(3,2) DEFAULT 5.00,
fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (id_producto) REFERENCES productos(id_producto) ON DELETE CASCADE,
FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

#-----------------------------------------------------------------#
# COMPRAS #
#-----------------------------------------------------------------#
#Registro de transacciones punto a punto
CREATE TABLE compras (
id_compra INT AUTO_INCREMENT PRIMARY KEY,
id_publicacion INT NOT NULL,
id_comprador INT NOT NULL,
#Usuario que compra
cantidad INT NOT NULL DEFAULT 1,
monto_total DECIMAL(10,2) NOT NULL,
tit_tarjeta VARCHAR(100),
num_tarjeta VARCHAR(30),
fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (id_publicacion) REFERENCES publicaciones(id_publicacion),
FOREIGN KEY (id_comprador) REFERENCES usuarios(id_usuario)
);

#-----------------------------------------------------------------#
# TESTEOS CON VIDEOJUEGOS #
#-----------------------------------------------------------------#

#Insertamos usuarios
INSERT INTO usuarios (nombre, email, contrasena, admin, descripcion, logo) VALUES
('Juan Pérez', 'juan@gmail.com', '1234', FALSE, 'Fanático de los RPG y coleccionista', 'juan.png'),
('Pedro Gómez', 'pedro@gmail.com', 'abcd', FALSE, 'Comprador casual de consolas', 'pedro.png'),
('Admin Tienda', 'admin@gmail.com', 'admin123', TRUE, 'Administrador del sistema', 'admin.png');
#Insertamos catálogo de videojuegos
INSERT INTO productos (nombre, descripcion, logo) VALUES
('Elden Ring', 'Juego de acción y rol de mundo abierto desarrollado por FromSoftware.', 'elden_ring.png'),
('Red Dead Redemption 2', 'Épica historia del salvaje oeste desarrollada por Rockstar Games.', 'rdr2.png'),
('God of War Ragnarök', 'Aventura nórdica de Kratos y Atreus.', 'gow_ragnarok.png');
#Publicaciones creadas por Juan (Vendedor)
INSERT INTO publicaciones (id_producto, id_usuario, stock, precio, descripcion_vendedor) VALUES
(1, 1, 5, 45000.00, 'Código digital para Steam
Entrega inmediata'),
(2, 1, 2, 38000.00, 'Juego físico para PS4
Excelente estado'),
(3, 1, 1, 52000.00, 'Juego físico para PS5
Sellado de fábrica');
#Compras realizadas por Pedro (Comprador)
INSERT INTO compras (id_publicacion, id_comprador, cantidad, monto_total, tit_tarjeta, num_tarjeta) VALUES
(1, 2, 1, 45000.00, 'Pedro Gómez', '4500123456789012'),
(3, 2, 1, 52000.00, 'Pedro Gómez', '5200123456789012');
#-----------------------------------------------------------------#
# CONSULTA #
#-----------------------------------------------------------------#

SELECT
c.id_compra,
u_comprador.nombre AS comprador,
prod.nombre AS videojuego,
u_vendedor.nombre AS vendedor,
c.monto_total,
c.fecha
FROM compras c
JOIN usuarios u_comprador ON c.id_comprador = u_comprador.id_usuario
JOIN publicaciones pub ON c.id_publicacion = pub.id_publicacion
JOIN productos prod ON pub.id_producto = prod.id_producto
JOIN usuarios u_vendedor ON pub.id_usuario = u_vendedor.id_usuario;