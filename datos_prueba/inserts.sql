-- =================================================================
-- SIGPDA - Datos de prueba (PostgreSQL)
-- =================================================================
-- Ejecutar después de aplicar `database/esquema.sql`.
-- Las contraseñas son hash bcrypt de los valores indicados como
-- comentario al lado de cada usuario.
-- =================================================================

BEGIN;

-- ----------------------------------------------------------------
-- ROLES
-- ----------------------------------------------------------------
INSERT INTO roles (nombre, descripcion, estado) VALUES
  ('Administrador', 'Acceso total al sistema', TRUE),
  ('Gerente',       'Gestión operativa y reportes', TRUE),
  ('Trabajador',    'Registro diario de operaciones', TRUE),
  ('Analista',      'Lectura, reportes y exportación', TRUE)
ON CONFLICT (nombre) DO NOTHING;

-- ----------------------------------------------------------------
-- USUARIOS
-- ----------------------------------------------------------------
-- Las claves bcrypt de abajo corresponden a:
--   admin     → admin123
--   gerente   → gerente123
--   trabajador→ trabajador123
--   analista  → analista123
-- (Si prefiere generarlas con bcrypt en vivo, ejecute mejor el
--  script Python `scripts/inicializar_bd.py`).
INSERT INTO usuarios (nombre, apellido, correo, usuario, contrasena, id_rol, estado)
VALUES
  ('Admin',  'Sistema', 'admin@sigpda.pe',     'admin',
   '$2b$12$KIXnEKx8tVB7s4l1.SkBG.dZmKpD8m3pQ2QhJ6c9rZ.JDqTZQyqU2',
   (SELECT id_rol FROM roles WHERE nombre = 'Administrador'), TRUE),
  ('Lucía',  'Pereda',  'gerente@sigpda.pe',   'gerente',
   '$2b$12$KIXnEKx8tVB7s4l1.SkBG.dZmKpD8m3pQ2QhJ6c9rZ.JDqTZQyqU2',
   (SELECT id_rol FROM roles WHERE nombre = 'Gerente'), TRUE),
  ('Manuel', 'Quispe',  'trabajador@sigpda.pe','trabajador',
   '$2b$12$KIXnEKx8tVB7s4l1.SkBG.dZmKpD8m3pQ2QhJ6c9rZ.JDqTZQyqU2',
   (SELECT id_rol FROM roles WHERE nombre = 'Trabajador'), TRUE),
  ('Sofía',  'Castro',  'analista@sigpda.pe',  'analista',
   '$2b$12$KIXnEKx8tVB7s4l1.SkBG.dZmKpD8m3pQ2QhJ6c9rZ.JDqTZQyqU2',
   (SELECT id_rol FROM roles WHERE nombre = 'Analista'), TRUE)
ON CONFLICT (usuario) DO NOTHING;

-- ----------------------------------------------------------------
-- RESTAURANTES (Valle Jequetepeque)
-- ----------------------------------------------------------------
INSERT INTO restaurantes (nombre_comercial, ruc, direccion, distrito, provincia, responsable, telefono, correo, estado) VALUES
  ('Cevichería El Pacífico',     '20512345678', 'Jr. Lima 245',       'Pacasmayo',         'Pacasmayo', 'Carlos Mendoza Sánchez', '044-521234', 'elpacifico@gmail.com',     TRUE),
  ('Restaurante Sabor Norteño',  '20623456789', 'Av. Bolognesi 512',  'San Pedro de Lloc', 'Pacasmayo', 'María Vásquez Ríos',     '044-577890', 'sabornorteno@hotmail.com', TRUE),
  ('El Rincón Guadalupano',      '20734567890', 'Calle Real 134',     'Guadalupe',         'Pacasmayo', 'Juan Pablo Cruz',        '044-562345', 'rinconguadalupano@gmail.com', TRUE),
  ('Picantería Chepenana',       '20845678901', 'Jr. Atahualpa 78',   'Chepén',            'Chepén',    'Rosa Linares Castro',    '044-562111', 'chepenana@gmail.com',      TRUE)
ON CONFLICT (ruc) DO NOTHING;

-- ----------------------------------------------------------------
-- PLATOS  (se insertan para el primer restaurante; el script
-- Python los replica en los demás)
-- ----------------------------------------------------------------
INSERT INTO platos (id_restaurante, nombre, categoria, precio_venta, costo_estimado, tiempo_preparacion_min, estado) VALUES
  (1, 'Cabrito a la Norteña',     'Especialidad regional', 28.00, 10.50, 35, TRUE),
  (1, 'Arroz con Pato',           'Plato de fondo',        25.00,  9.20, 40, TRUE),
  (1, 'Ceviche Mixto',            'Plato de fondo',        22.00,  8.00, 15, TRUE),
  (1, 'Ceviche de Pescado',       'Plato de fondo',        20.00,  7.00, 12, TRUE),
  (1, 'Seco de Cabrito',          'Especialidad regional', 26.00,  9.50, 30, TRUE),
  (1, 'Causa Limeña',             'Entrada',               12.00,  4.00, 15, TRUE),
  (1, 'Sopa Shámbar',             'Sopa',                  15.00,  5.50, 25, TRUE),
  (1, 'Chicharrón de Pescado',    'Plato de fondo',        24.00,  8.50, 20, TRUE),
  (1, 'Arroz a la Marinera',      'Plato de fondo',        26.00,  9.00, 25, TRUE),
  (1, 'Tallarín Saltado',         'Plato de fondo',        18.00,  6.50, 18, TRUE),
  (1, 'Lomo Saltado',             'Plato de fondo',        22.00,  8.50, 20, TRUE),
  (1, 'Sudado de Pescado',        'Plato de fondo',        23.00,  8.00, 25, TRUE),
  (1, 'Arroz con Mariscos',       'Plato de fondo',        27.00, 10.00, 25, TRUE),
  (1, 'King Kong',                'Postre',                 8.00,  2.50,  5, TRUE),
  (1, 'Suspiro Limeño',           'Postre',                 7.00,  2.00, 10, TRUE),
  (1, 'Chicha Morada (jarra)',    'Bebida',                 8.00,  2.00,  5, TRUE),
  (1, 'Inca Kola personal',       'Bebida',                 4.00,  2.00,  1, TRUE),
  (1, 'Jugo de Maracuyá',         'Bebida',                 6.00,  2.00,  5, TRUE),
  (1, 'Combo Marino',             'Combo',                 35.00, 13.00, 25, TRUE),
  (1, 'Combo Norteño',            'Combo',                 32.00, 12.00, 30, TRUE);

-- ----------------------------------------------------------------
-- INSUMOS
-- ----------------------------------------------------------------
INSERT INTO insumos (id_restaurante, nombre, categoria, unidad_medida, stock_disponible, stock_minimo, costo_unitario, fecha_vencimiento, proveedor, estado) VALUES
  (1, 'Pescado Cabrilla',     'Pescados',  'kg',     8.5, 3.0, 18.00, CURRENT_DATE + 5,   'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Pescado Bonito',       'Pescados',  'kg',     6.0, 2.0, 14.00, CURRENT_DATE + 3,   'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Calamar',              'Mariscos',  'kg',     4.0, 1.5, 25.00, CURRENT_DATE + 30,  'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Langostinos',          'Mariscos',  'kg',     3.0, 1.0, 35.00, CURRENT_DATE + 20,  'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Conchas de Abanico',   'Mariscos',  'kg',     2.5, 1.0, 28.00, CURRENT_DATE + 15,  'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Carne de Cabrito',     'Carnes',    'kg',     6.0, 2.0, 22.00, CURRENT_DATE + 7,   'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Pato entero',          'Carnes',    'unidad', 8.0, 3.0, 28.00, CURRENT_DATE + 10,  'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Carne de Res (lomo)',  'Carnes',    'kg',     5.0, 2.0, 26.00, CURRENT_DATE + 8,   'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Pollo entero',         'Carnes',    'kg',    10.0, 4.0, 12.00, CURRENT_DATE + 4,   'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Arroz Costeño',        'Granos',    'kg',    50.0,15.0,  4.50, CURRENT_DATE + 180, 'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Frijol Caballero',     'Granos',    'kg',    12.0, 4.0,  8.00, CURRENT_DATE + 120, 'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Maíz Morado',          'Granos',    'kg',     5.0, 2.0,  6.50, CURRENT_DATE + 90,  'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Cebolla Roja',         'Verduras',  'kg',    15.0, 5.0,  3.00, CURRENT_DATE + 12,  'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Tomate',               'Verduras',  'kg',    10.0, 3.0,  3.50, CURRENT_DATE + 6,   'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Limón Sutil',          'Verduras',  'kg',     8.0, 3.0,  5.00, CURRENT_DATE + 9,   'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Ají Amarillo',         'Verduras',  'kg',     4.0, 1.5,  7.00, CURRENT_DATE + 7,   'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Ají Limo',             'Verduras',  'kg',     2.0, 1.0,  9.00, CURRENT_DATE + 6,   'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Camote',               'Verduras',  'kg',     8.0, 3.0,  2.50, CURRENT_DATE + 18,  'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Yuca',                 'Verduras',  'kg',     6.0, 2.0,  2.00, CURRENT_DATE + 15,  'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Cilantro',             'Verduras',  'atado', 12.0, 5.0,  1.00, CURRENT_DATE + 4,   'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Culantro',             'Verduras',  'atado', 10.0, 4.0,  1.00, CURRENT_DATE + 4,   'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Loche',                'Verduras',  'kg',     3.0, 1.0,  6.00, CURRENT_DATE + 12,  'Mercado Mayorista Pacasmayo', TRUE),
  (1, 'Aceite vegetal',       'Abarrotes', 'lt',    18.0, 5.0,  8.00, CURRENT_DATE + 365, 'Distribuidora Norte',         TRUE),
  (1, 'Sal',                  'Abarrotes', 'kg',     8.0, 2.0,  1.50, CURRENT_DATE + 720, 'Distribuidora Norte',         TRUE),
  (1, 'Comino molido',        'Abarrotes', 'kg',     0.5, 0.2, 35.00, CURRENT_DATE + 365, 'Distribuidora Norte',         TRUE),
  (1, 'Pimienta molida',      'Abarrotes', 'kg',     0.4, 0.2, 40.00, CURRENT_DATE + 365, 'Distribuidora Norte',         TRUE),
  (1, 'Vinagre',              'Abarrotes', 'lt',     6.0, 2.0,  5.00, CURRENT_DATE + 240, 'Distribuidora Norte',         TRUE),
  (1, 'Chicha de Jora',       'Abarrotes', 'lt',     4.0, 2.0,  4.50, CURRENT_DATE + 30,  'Distribuidora Norte',         TRUE),
  (1, 'Manjar Blanco',        'Postres',   'kg',     3.0, 1.0, 12.00, CURRENT_DATE + 14,  'Distribuidora Norte',         TRUE),
  (1, 'Galleta King Kong',    'Postres',   'kg',     2.0, 1.0, 10.00, CURRENT_DATE + 60,  'Distribuidora Norte',         TRUE);

-- ----------------------------------------------------------------
-- CONFIGURACIÓN
-- ----------------------------------------------------------------
INSERT INTO configuracion (clave, valor, descripcion) VALUES
  ('umbral_desperdicio',         '15',    'Umbral máximo de % de desperdicio permitido'),
  ('moneda',                     'S/',    'Símbolo de moneda'),
  ('nombre_sistema',             'SIGPDA','Nombre del sistema'),
  ('duracion_sesion_minutos',    '120',   'Tiempo de sesión activa (min)'),
  ('formato_reporte',            'PDF',   'Formato preferido de reportes'),
  ('n8n_habilitado',             'true',  'Habilitar webhook n8n')
ON CONFLICT (clave) DO NOTHING;

COMMIT;

-- =================================================================
-- NOTA: Para generar las ventas históricas (90 días) y datos de IA,
-- ejecute el script Python:
--    python -m scripts.inicializar_bd
-- =================================================================
