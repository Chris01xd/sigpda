-- =================================================================
-- SIGPDA - SCRIPT DE CREACIÓN DE BASE DE DATOS
-- Sistema Inteligente de Gestión y Predicción de Desperdicio Alimentario
-- Motor: PostgreSQL 13+
-- Todos los nombres en ESPAÑOL
-- =================================================================

-- Si la BD existe, borrar para reinstalar (ejecutar fuera de la BD)
-- DROP DATABASE IF EXISTS sigpda;
-- CREATE DATABASE sigpda;
-- \c sigpda;

-- =================================================================
-- 1. ROLES
-- =================================================================
CREATE TABLE IF NOT EXISTS roles (
    id_rol           SERIAL PRIMARY KEY,
    nombre           VARCHAR(50) UNIQUE NOT NULL,
    descripcion      VARCHAR(255),
    estado           BOOLEAN DEFAULT TRUE,
    fecha_creacion   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- 2. PERMISOS
-- =================================================================
CREATE TABLE IF NOT EXISTS permisos (
    id_permiso       SERIAL PRIMARY KEY,
    id_rol           INT NOT NULL REFERENCES roles(id_rol) ON DELETE CASCADE,
    modulo           VARCHAR(50) NOT NULL,
    accion           VARCHAR(30) NOT NULL  -- ver/crear/editar/eliminar/exportar/generar_reporte
);

-- =================================================================
-- 3. USUARIOS
-- =================================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario       SERIAL PRIMARY KEY,
    nombre           VARCHAR(80) NOT NULL,
    apellido         VARCHAR(80) NOT NULL,
    correo           VARCHAR(120) UNIQUE NOT NULL,
    usuario          VARCHAR(60) UNIQUE NOT NULL,
    contrasena       VARCHAR(255) NOT NULL,
    id_rol           INT NOT NULL REFERENCES roles(id_rol),
    estado           BOOLEAN DEFAULT TRUE,
    fecha_creacion   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso    TIMESTAMP
);

-- =================================================================
-- 4. SESIONES
-- =================================================================
CREATE TABLE IF NOT EXISTS sesiones (
    id_sesion        SERIAL PRIMARY KEY,
    id_usuario       INT NOT NULL REFERENCES usuarios(id_usuario),
    fecha_ingreso    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_salida     TIMESTAMP,
    ip_equipo        VARCHAR(45),
    estado           VARCHAR(20) DEFAULT 'activa'
);

-- =================================================================
-- 5. RESTAURANTES (PyMEs Gastronómicas)
-- =================================================================
CREATE TABLE IF NOT EXISTS restaurantes (
    id_restaurante   SERIAL PRIMARY KEY,
    nombre_comercial VARCHAR(150) NOT NULL,
    ruc              VARCHAR(15) UNIQUE,
    direccion        VARCHAR(200),
    distrito         VARCHAR(80),
    provincia        VARCHAR(80),
    responsable      VARCHAR(150),
    telefono         VARCHAR(20),
    correo           VARCHAR(120),
    estado           BOOLEAN DEFAULT TRUE,
    fecha_registro   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- 6. PLATOS
-- =================================================================
CREATE TABLE IF NOT EXISTS platos (
    id_plato                 SERIAL PRIMARY KEY,
    id_restaurante           INT REFERENCES restaurantes(id_restaurante),
    nombre                   VARCHAR(120) NOT NULL,
    categoria                VARCHAR(60),
    descripcion              TEXT,
    precio_venta             NUMERIC(10,2) NOT NULL,
    costo_estimado           NUMERIC(10,2) DEFAULT 0,
    tiempo_preparacion_min   INT DEFAULT 0,
    estado                   BOOLEAN DEFAULT TRUE,
    fecha_creacion           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- 7. INSUMOS
-- =================================================================
CREATE TABLE IF NOT EXISTS insumos (
    id_insumo            SERIAL PRIMARY KEY,
    id_restaurante       INT REFERENCES restaurantes(id_restaurante),
    nombre               VARCHAR(120) NOT NULL,
    categoria            VARCHAR(60),
    unidad_medida        VARCHAR(20) NOT NULL,
    stock_disponible     NUMERIC(10,3) DEFAULT 0,
    stock_minimo         NUMERIC(10,3) DEFAULT 0,
    costo_unitario       NUMERIC(10,2) DEFAULT 0,
    fecha_vencimiento    DATE,
    proveedor            VARCHAR(120),
    estado               BOOLEAN DEFAULT TRUE,
    fecha_creacion       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- 8. RECETAS (relación plato-insumo)
-- =================================================================
CREATE TABLE IF NOT EXISTS recetas (
    id_receta        SERIAL PRIMARY KEY,
    id_plato         INT NOT NULL REFERENCES platos(id_plato) ON DELETE CASCADE,
    id_insumo        INT NOT NULL REFERENCES insumos(id_insumo),
    cantidad_usada   NUMERIC(10,3) NOT NULL,
    unidad_medida    VARCHAR(20),
    fecha_creacion   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- 9. VENTAS
-- =================================================================
CREATE TABLE IF NOT EXISTS ventas (
    id_venta         SERIAL PRIMARY KEY,
    id_restaurante   INT REFERENCES restaurantes(id_restaurante),
    id_usuario       INT REFERENCES usuarios(id_usuario),
    fecha            DATE DEFAULT CURRENT_DATE,
    hora             VARCHAR(8),
    total            NUMERIC(12,2) DEFAULT 0,
    metodo_pago      VARCHAR(30) DEFAULT 'efectivo',
    observaciones    TEXT,
    fecha_registro   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- 10. DETALLE DE VENTAS
-- =================================================================
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id_detalle       SERIAL PRIMARY KEY,
    id_venta         INT NOT NULL REFERENCES ventas(id_venta) ON DELETE CASCADE,
    id_plato         INT NOT NULL REFERENCES platos(id_plato),
    cantidad         INT NOT NULL,
    precio_unitario  NUMERIC(10,2) NOT NULL,
    subtotal         NUMERIC(12,2) NOT NULL
);

-- =================================================================
-- 11. PRODUCCIÓN
-- =================================================================
CREATE TABLE IF NOT EXISTS producciones (
    id_produccion        SERIAL PRIMARY KEY,
    id_restaurante       INT REFERENCES restaurantes(id_restaurante),
    id_plato             INT NOT NULL REFERENCES platos(id_plato),
    id_usuario           INT REFERENCES usuarios(id_usuario),
    fecha                DATE DEFAULT CURRENT_DATE,
    cantidad_preparada   INT NOT NULL,
    cantidad_vendida     INT DEFAULT 0,
    cantidad_sobrante    INT DEFAULT 0,
    observaciones        TEXT,
    fecha_registro       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- 12. DESPERDICIOS
-- =================================================================
CREATE TABLE IF NOT EXISTS desperdicios (
    id_desperdicio   SERIAL PRIMARY KEY,
    id_restaurante   INT REFERENCES restaurantes(id_restaurante),
    id_plato         INT REFERENCES platos(id_plato),
    id_insumo        INT REFERENCES insumos(id_insumo),
    id_usuario       INT REFERENCES usuarios(id_usuario),
    fecha            DATE DEFAULT CURRENT_DATE,
    tipo             VARCHAR(20),  -- plato | insumo
    cantidad         NUMERIC(10,3) NOT NULL,
    unidad_medida    VARCHAR(20),
    motivo           VARCHAR(60) NOT NULL,
    costo_estimado   NUMERIC(10,2) DEFAULT 0,
    observaciones    TEXT,
    fecha_registro   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- 13. PREDICCIONES
-- =================================================================
CREATE TABLE IF NOT EXISTS predicciones (
    id_prediccion              SERIAL PRIMARY KEY,
    id_restaurante             INT REFERENCES restaurantes(id_restaurante),
    id_plato                   INT NOT NULL REFERENCES platos(id_plato),
    fecha_objetivo             DATE NOT NULL,
    demanda_estimada           FLOAT NOT NULL,
    recomendacion_produccion   INT NOT NULL,
    riesgo_desperdicio         VARCHAR(20),
    modelo_usado               VARCHAR(50),
    mae                        FLOAT,
    r2                         FLOAT,
    confianza                  FLOAT,
    fecha_generacion           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_usuario                 INT REFERENCES usuarios(id_usuario)
);

-- =================================================================
-- 14. BITÁCORA
-- =================================================================
CREATE TABLE IF NOT EXISTS bitacora (
    id_bitacora      SERIAL PRIMARY KEY,
    id_usuario       INT REFERENCES usuarios(id_usuario),
    usuario_nombre   VARCHAR(120),
    rol              VARCHAR(50),
    modulo           VARCHAR(60) NOT NULL,
    accion           VARCHAR(60) NOT NULL,
    descripcion      TEXT,
    fecha            DATE DEFAULT CURRENT_DATE,
    hora             VARCHAR(8),
    ip_equipo        VARCHAR(45),
    resultado        VARCHAR(20) DEFAULT 'éxito'
);

-- =================================================================
-- 15. CONFIGURACIÓN
-- =================================================================
CREATE TABLE IF NOT EXISTS configuracion (
    id_configuracion     SERIAL PRIMARY KEY,
    clave                VARCHAR(80) UNIQUE NOT NULL,
    valor                VARCHAR(255),
    descripcion          VARCHAR(255),
    fecha_actualizacion  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- 16. ALERTAS (auxiliar para n8n)
-- =================================================================
CREATE TABLE IF NOT EXISTS alertas (
    id_alerta        SERIAL PRIMARY KEY,
    tipo             VARCHAR(60),
    titulo           VARCHAR(150),
    mensaje          TEXT,
    severidad        VARCHAR(20),
    enviado_n8n      BOOLEAN DEFAULT FALSE,
    fecha_creacion   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_envio      TIMESTAMP,
    id_restaurante   INT REFERENCES restaurantes(id_restaurante)
);

-- =================================================================
-- ÍNDICES PARA RENDIMIENTO
-- =================================================================
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha);
CREATE INDEX IF NOT EXISTS idx_desperdicios_fecha ON desperdicios(fecha);
CREATE INDEX IF NOT EXISTS idx_producciones_fecha ON producciones(fecha);
CREATE INDEX IF NOT EXISTS idx_bitacora_fecha ON bitacora(fecha);
CREATE INDEX IF NOT EXISTS idx_insumos_vencimiento ON insumos(fecha_vencimiento);
CREATE INDEX IF NOT EXISTS idx_predicciones_fecha ON predicciones(fecha_objetivo);
