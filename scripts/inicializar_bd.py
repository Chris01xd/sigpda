"""
=================================================================
SIGPDA - Inicialización de BD y carga de datos de prueba
=================================================================
Este script crea las tablas y carga datos de prueba realistas
del Valle Jequetepeque (Pacasmayo, San Pedro de Lloc, Guadalupe,
Chepén). Genera 90 días de ventas históricas para entrenar la IA.

Ejecutar desde la raíz del proyecto:
    python -m scripts.inicializar_bd
"""

import sys
import os
import random
from datetime import datetime, date, timedelta, time
from pathlib import Path

# Permitir ejecución como script independiente
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bcrypt

from database import crear_tablas, obtener_sesion
from database.modelos import (
    Rol, Permiso, Usuario, Restaurante, Plato, Insumo, Receta,
    Venta, DetalleVenta, Produccion, Desperdicio, Configuracion
)
from config.settings import (
    PERMISOS_POR_ROL, MOTIVOS_DESPERDICIO,
    UMBRAL_DESPERDICIO_PORCENTAJE, MONEDA, NOMBRE_SISTEMA
)


def _hash(p: str) -> str:
    return bcrypt.hashpw(p.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ----------------------------------------------------------------
# DATOS BASE
# ----------------------------------------------------------------
RESTAURANTES_DATA = [
    {
        "nombre_comercial": "Cevichería El Pacífico",
        "ruc": "20512345678",
        "direccion": "Jr. Lima 245",
        "distrito": "Pacasmayo",
        "provincia": "Pacasmayo",
        "responsable": "Carlos Mendoza Sánchez",
        "telefono": "044-521234",
        "correo": "elpacifico@gmail.com",
    },
    {
        "nombre_comercial": "Restaurante Sabor Norteño",
        "ruc": "20623456789",
        "direccion": "Av. Bolognesi 512",
        "distrito": "San Pedro de Lloc",
        "provincia": "Pacasmayo",
        "responsable": "María Vásquez Ríos",
        "telefono": "044-577890",
        "correo": "sabornorteno@hotmail.com",
    },
    {
        "nombre_comercial": "El Rincón Guadalupano",
        "ruc": "20734567890",
        "direccion": "Calle Real 134",
        "distrito": "Guadalupe",
        "provincia": "Pacasmayo",
        "responsable": "Juan Pablo Cruz",
        "telefono": "044-562345",
        "correo": "rinconguadalupano@gmail.com",
    },
    {
        "nombre_comercial": "Picantería Chepenana",
        "ruc": "20845678901",
        "direccion": "Jr. Atahualpa 78",
        "distrito": "Chepén",
        "provincia": "Chepén",
        "responsable": "Rosa Linares Castro",
        "telefono": "044-562111",
        "correo": "chepenana@gmail.com",
    },
]

PLATOS_DATA = [
    # (nombre, categoría, precio, costo, tiempo_min)
    ("Cabrito a la Norteña", "Especialidad regional", 28.00, 10.50, 35),
    ("Arroz con Pato", "Plato de fondo", 25.00, 9.20, 40),
    ("Ceviche Mixto", "Plato de fondo", 22.00, 8.00, 15),
    ("Ceviche de Pescado", "Plato de fondo", 20.00, 7.00, 12),
    ("Seco de Cabrito", "Especialidad regional", 26.00, 9.50, 30),
    ("Causa Limeña", "Entrada", 12.00, 4.00, 15),
    ("Sopa Shámbar", "Sopa", 15.00, 5.50, 25),
    ("Chicharrón de Pescado", "Plato de fondo", 24.00, 8.50, 20),
    ("Arroz a la Marinera", "Plato de fondo", 26.00, 9.00, 25),
    ("Tallarín Saltado", "Plato de fondo", 18.00, 6.50, 18),
    ("Lomo Saltado", "Plato de fondo", 22.00, 8.50, 20),
    ("Sudado de Pescado", "Plato de fondo", 23.00, 8.00, 25),
    ("Arroz con Mariscos", "Plato de fondo", 27.00, 10.00, 25),
    ("King Kong", "Postre", 8.00, 2.50, 5),
    ("Suspiro Limeño", "Postre", 7.00, 2.00, 10),
    ("Chicha Morada (jarra)", "Bebida", 8.00, 2.00, 5),
    ("Inca Kola personal", "Bebida", 4.00, 2.00, 1),
    ("Jugo de Maracuyá", "Bebida", 6.00, 2.00, 5),
    ("Combo Marino", "Combo", 35.00, 13.00, 25),
    ("Combo Norteño", "Combo", 32.00, 12.00, 30),
]

INSUMOS_DATA = [
    # (nombre, categoría, unidad, stock, stock_min, costo)
    ("Pescado Cabrilla", "Pescados", "kg", 8.5, 3.0, 18.00),
    ("Pescado Bonito", "Pescados", "kg", 6.0, 2.0, 14.00),
    ("Calamar", "Mariscos", "kg", 4.0, 1.5, 25.00),
    ("Langostinos", "Mariscos", "kg", 3.0, 1.0, 35.00),
    ("Conchas de Abanico", "Mariscos", "kg", 2.5, 1.0, 28.00),
    ("Carne de Cabrito", "Carnes", "kg", 6.0, 2.0, 22.00),
    ("Pato entero", "Carnes", "unidad", 8.0, 3.0, 28.00),
    ("Carne de Res (lomo)", "Carnes", "kg", 5.0, 2.0, 26.00),
    ("Pollo entero", "Carnes", "kg", 10.0, 4.0, 12.00),
    ("Arroz Costeño", "Granos", "kg", 50.0, 15.0, 4.50),
    ("Frijol Caballero", "Granos", "kg", 12.0, 4.0, 8.00),
    ("Maíz Morado", "Granos", "kg", 5.0, 2.0, 6.50),
    ("Cebolla Roja", "Verduras", "kg", 15.0, 5.0, 3.00),
    ("Tomate", "Verduras", "kg", 10.0, 3.0, 3.50),
    ("Limón Sutil", "Verduras", "kg", 8.0, 3.0, 5.00),
    ("Ají Amarillo", "Verduras", "kg", 4.0, 1.5, 7.00),
    ("Ají Limo", "Verduras", "kg", 2.0, 1.0, 9.00),
    ("Camote", "Verduras", "kg", 8.0, 3.0, 2.50),
    ("Yuca", "Verduras", "kg", 6.0, 2.0, 2.00),
    ("Cilantro", "Verduras", "atado", 12.0, 5.0, 1.00),
    ("Culantro", "Verduras", "atado", 10.0, 4.0, 1.00),
    ("Loche", "Verduras", "kg", 3.0, 1.0, 6.00),
    ("Aceite vegetal", "Abarrotes", "lt", 18.0, 5.0, 8.00),
    ("Sal", "Abarrotes", "kg", 8.0, 2.0, 1.50),
    ("Comino molido", "Abarrotes", "kg", 0.5, 0.2, 35.00),
    ("Pimienta molida", "Abarrotes", "kg", 0.4, 0.2, 40.00),
    ("Vinagre", "Abarrotes", "lt", 6.0, 2.0, 5.00),
    ("Chicha de Jora", "Abarrotes", "lt", 4.0, 2.0, 4.50),
    ("Manjar Blanco", "Postres", "kg", 3.0, 1.0, 12.00),
    ("Galleta King Kong", "Postres", "kg", 2.0, 1.0, 10.00),
]


def crear_roles_y_permisos(sesion) -> dict:
    """Crea los 4 roles base y carga sus permisos según settings."""
    print("→ Creando roles y permisos...")
    roles_obj = {}
    descripciones = {
        "Administrador": "Acceso total al sistema",
        "Gerente": "Gestión operativa y reportes",
        "Trabajador": "Registro diario de operaciones",
        "Analista": "Lectura, reportes y exportación",
    }
    for nombre_rol in PERMISOS_POR_ROL.keys():
        rol = sesion.query(Rol).filter(Rol.nombre == nombre_rol).first()
        if not rol:
            rol = Rol(nombre=nombre_rol,
                       descripcion=descripciones.get(nombre_rol, ""))
            sesion.add(rol)
            sesion.flush()
        roles_obj[nombre_rol] = rol

        # Cargar permisos
        permisos = PERMISOS_POR_ROL[nombre_rol]
        if "todos" in permisos:
            modulos_universales = [
                "usuarios", "roles", "restaurantes", "platos", "insumos",
                "recetas", "ventas", "produccion", "desperdicio", "prediccion",
                "recomendaciones", "dashboard", "estadisticas", "reportes",
                "bitacora", "configuracion",
            ]
            for m in modulos_universales:
                for accion in permisos["todos"]:
                    if not sesion.query(Permiso).filter(
                        Permiso.id_rol == rol.id_rol,
                        Permiso.modulo == m,
                        Permiso.accion == accion,
                    ).first():
                        sesion.add(Permiso(id_rol=rol.id_rol, modulo=m, accion=accion))
        else:
            for modulo, acciones in permisos.items():
                for accion in acciones:
                    if not sesion.query(Permiso).filter(
                        Permiso.id_rol == rol.id_rol,
                        Permiso.modulo == modulo,
                        Permiso.accion == accion,
                    ).first():
                        sesion.add(Permiso(id_rol=rol.id_rol, modulo=modulo, accion=accion))
    sesion.commit()
    return roles_obj


def crear_usuarios(sesion, roles: dict) -> None:
    """Crea los 4 usuarios de prueba."""
    print("→ Creando usuarios de prueba...")
    usuarios_data = [
        ("Admin", "Sistema", "admin@sigpda.pe", "admin", "admin123", "Administrador"),
        ("Lucía", "Pereda", "gerente@sigpda.pe", "gerente", "gerente123", "Gerente"),
        ("Manuel", "Quispe", "trabajador@sigpda.pe", "trabajador", "trabajador123", "Trabajador"),
        ("Sofía", "Castro", "analista@sigpda.pe", "analista", "analista123", "Analista"),
    ]
    for nombre, apellido, correo, usuario, pwd, rol_nombre in usuarios_data:
        existente = sesion.query(Usuario).filter(Usuario.usuario == usuario).first()
        if not existente:
            sesion.add(Usuario(
                nombre=nombre, apellido=apellido, correo=correo,
                usuario=usuario, contrasena=_hash(pwd),
                id_rol=roles[rol_nombre].id_rol,
                estado=True,
            ))
    sesion.commit()


def crear_restaurantes(sesion) -> list:
    print("→ Creando restaurantes...")
    creados = []
    for r in RESTAURANTES_DATA:
        ex = sesion.query(Restaurante).filter(Restaurante.ruc == r["ruc"]).first()
        if not ex:
            obj = Restaurante(**r, estado=True)
            sesion.add(obj)
            sesion.flush()
            creados.append(obj)
        else:
            creados.append(ex)
    sesion.commit()
    return creados


def crear_platos(sesion, restaurantes: list) -> list:
    print("→ Creando platos...")
    creados = []
    for r in restaurantes:
        for nombre, cat, precio, costo, tiempo in PLATOS_DATA:
            ex = sesion.query(Plato).filter(
                Plato.id_restaurante == r.id_restaurante,
                Plato.nombre == nombre,
            ).first()
            if not ex:
                obj = Plato(
                    id_restaurante=r.id_restaurante,
                    nombre=nombre, categoria=cat,
                    precio_venta=precio, costo_estimado=costo,
                    tiempo_preparacion_min=tiempo, estado=True,
                )
                sesion.add(obj)
                sesion.flush()
                creados.append(obj)
            else:
                creados.append(ex)
    sesion.commit()
    return creados


def crear_insumos(sesion, restaurantes: list) -> list:
    print("→ Creando insumos...")
    hoy = date.today()
    creados = []
    for r in restaurantes:
        for i, (nombre, cat, unidad, stock, stock_min, costo) in enumerate(INSUMOS_DATA):
            ex = sesion.query(Insumo).filter(
                Insumo.id_restaurante == r.id_restaurante,
                Insumo.nombre == nombre,
            ).first()
            if not ex:
                # Vencimientos variados (algunos próximos para alertas)
                if i % 7 == 0:
                    venc = hoy + timedelta(days=random.randint(2, 7))   # próximos
                elif i % 11 == 0:
                    venc = hoy - timedelta(days=random.randint(1, 3))   # vencidos
                else:
                    venc = hoy + timedelta(days=random.randint(15, 90))
                obj = Insumo(
                    id_restaurante=r.id_restaurante,
                    nombre=nombre, categoria=cat, unidad_medida=unidad,
                    stock_disponible=stock, stock_minimo=stock_min,
                    costo_unitario=costo, fecha_vencimiento=venc,
                    proveedor="Mercado Mayorista Pacasmayo",
                    estado=True,
                )
                sesion.add(obj)
                sesion.flush()
                creados.append(obj)
            else:
                creados.append(ex)
    sesion.commit()
    return creados


def crear_recetas(sesion, platos: list, insumos: list) -> None:
    print("→ Creando recetas básicas...")
    # Mapeo simplificado plato → insumos (por nombre)
    mapa = {
        "Cabrito a la Norteña": [("Carne de Cabrito", 0.4, "kg"),
                                   ("Cebolla Roja", 0.1, "kg"),
                                   ("Ají Amarillo", 0.05, "kg"),
                                   ("Culantro", 0.5, "atado"),
                                   ("Loche", 0.05, "kg")],
        "Arroz con Pato": [("Pato entero", 0.25, "unidad"),
                              ("Arroz Costeño", 0.2, "kg"),
                              ("Cilantro", 0.5, "atado"),
                              ("Cebolla Roja", 0.1, "kg")],
        "Ceviche Mixto": [("Pescado Cabrilla", 0.15, "kg"),
                            ("Calamar", 0.05, "kg"),
                            ("Langostinos", 0.05, "kg"),
                            ("Limón Sutil", 0.1, "kg"),
                            ("Ají Limo", 0.02, "kg"),
                            ("Camote", 0.15, "kg")],
        "Ceviche de Pescado": [("Pescado Cabrilla", 0.2, "kg"),
                                  ("Limón Sutil", 0.1, "kg"),
                                  ("Cebolla Roja", 0.05, "kg"),
                                  ("Camote", 0.15, "kg")],
        "Lomo Saltado": [("Carne de Res (lomo)", 0.2, "kg"),
                            ("Cebolla Roja", 0.1, "kg"),
                            ("Tomate", 0.1, "kg"),
                            ("Arroz Costeño", 0.15, "kg")],
        "Chicha Morada (jarra)": [("Maíz Morado", 0.2, "kg")],
        "King Kong": [("Galleta King Kong", 0.1, "kg"),
                       ("Manjar Blanco", 0.05, "kg")],
    }
    # Por cada plato (independiente del restaurante)
    for plato in platos:
        if plato.nombre in mapa:
            for ins_nombre, cant, unidad in mapa[plato.nombre]:
                # Buscar insumo del mismo restaurante
                ins = next((i for i in insumos
                            if i.nombre == ins_nombre
                            and i.id_restaurante == plato.id_restaurante), None)
                if ins:
                    ex = sesion.query(Receta).filter(
                        Receta.id_plato == plato.id_plato,
                        Receta.id_insumo == ins.id_insumo,
                    ).first()
                    if not ex:
                        sesion.add(Receta(
                            id_plato=plato.id_plato,
                            id_insumo=ins.id_insumo,
                            cantidad_usada=cant,
                            unidad_medida=unidad,
                        ))
    sesion.commit()


def crear_ventas_historicas(sesion, restaurantes: list, platos: list,
                              usuarios: list, dias: int = 90) -> None:
    """Genera ventas, producciones y desperdicios para `dias` días."""
    print(f"→ Generando {dias} días de ventas históricas (puede tardar)...")
    random.seed(42)
    hoy = date.today()
    user_trabajador = next((u for u in usuarios if u.usuario == "trabajador"), usuarios[0])

    # Filtrar platos por restaurante
    platos_por_rest = {}
    for p in platos:
        platos_por_rest.setdefault(p.id_restaurante, []).append(p)

    for rest in restaurantes:
        platos_r = platos_por_rest.get(rest.id_restaurante, [])
        if not platos_r:
            continue

        for delta in range(dias, 0, -1):
            fecha_v = hoy - timedelta(days=delta)
            dow = fecha_v.weekday()  # 0=lunes, 6=domingo

            # Demanda mayor fines de semana
            num_tickets = random.randint(15, 35) if dow >= 5 else random.randint(8, 20)
            ventas_dia_total = 0

            for _ in range(num_tickets):
                hora = time(
                    hour=random.choice([12, 13, 14, 19, 20, 21]),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                )
                venta = Venta(
                    id_restaurante=rest.id_restaurante,
                    id_usuario=user_trabajador.id_usuario,
                    fecha=fecha_v,
                    hora=hora.strftime("%H:%M:%S"),
                    total=0,
                    metodo_pago=random.choice(["efectivo", "yape", "tarjeta", "plin"]),
                )
                sesion.add(venta)
                sesion.flush()

                # 1-4 platos por ticket
                total_ticket = 0
                for _ in range(random.randint(1, 4)):
                    plato = random.choice(platos_r)
                    cant = random.randint(1, 3)
                    sub = float(plato.precio_venta) * cant
                    sesion.add(DetalleVenta(
                        id_venta=venta.id_venta,
                        id_plato=plato.id_plato,
                        cantidad=cant,
                        precio_unitario=plato.precio_venta,
                        subtotal=sub,
                    ))
                    total_ticket += sub
                venta.total = total_ticket
                ventas_dia_total += total_ticket

            # Producción y desperdicio aleatorio (~60% de los días)
            if random.random() < 0.6:
                plato_prod = random.choice(platos_r)
                cant_prep = random.randint(15, 40)
                cant_vend = random.randint(int(cant_prep * 0.6), cant_prep)
                cant_sob = cant_prep - cant_vend
                sesion.add(Produccion(
                    id_restaurante=rest.id_restaurante,
                    id_plato=plato_prod.id_plato,
                    id_usuario=user_trabajador.id_usuario,
                    fecha=fecha_v,
                    cantidad_preparada=cant_prep,
                    cantidad_vendida=cant_vend,
                    cantidad_sobrante=cant_sob,
                    observaciones="",
                ))
                # Si hubo sobrante alto, registrar desperdicio
                if cant_sob > cant_prep * 0.15:
                    sesion.add(Desperdicio(
                        id_restaurante=rest.id_restaurante,
                        id_plato=plato_prod.id_plato,
                        id_usuario=user_trabajador.id_usuario,
                        fecha=fecha_v,
                        tipo="plato",
                        cantidad=cant_sob,
                        unidad_medida="porción",
                        motivo=random.choice(MOTIVOS_DESPERDICIO),
                        costo_estimado=cant_sob * float(plato_prod.costo_estimado),
                        observaciones="",
                    ))
        sesion.commit()
        print(f"   ✓ {rest.nombre_comercial}")


def crear_configuracion(sesion) -> None:
    print("→ Creando configuración inicial...")
    pares = {
        "umbral_desperdicio": str(UMBRAL_DESPERDICIO_PORCENTAJE),
        "moneda": MONEDA,
        "nombre_sistema": NOMBRE_SISTEMA,
        "duracion_sesion_minutos": "120",
        "formato_reporte": "PDF",
        "n8n_habilitado": "true",
    }
    for clave, valor in pares.items():
        ex = sesion.query(Configuracion).filter(Configuracion.clave == clave).first()
        if not ex:
            sesion.add(Configuracion(clave=clave, valor=valor,
                                       descripcion=f"Configuración para {clave}"))
    sesion.commit()


def main(dias_historicos: int = 90) -> None:
    print("=" * 60)
    print("SIGPDA - Inicialización de base de datos")
    print("=" * 60)

    crear_tablas()
    print("✓ Tablas creadas")

    sesion = obtener_sesion()
    try:
        roles = crear_roles_y_permisos(sesion)
        crear_usuarios(sesion, roles)
        usuarios = sesion.query(Usuario).all()

        restaurantes = crear_restaurantes(sesion)
        platos = crear_platos(sesion, restaurantes)
        insumos = crear_insumos(sesion, restaurantes)
        crear_recetas(sesion, platos, insumos)
        crear_configuracion(sesion)

        # ¿Ya hay ventas? Si sí, no regenerar.
        if sesion.query(Venta).count() == 0:
            crear_ventas_historicas(sesion, restaurantes, platos, usuarios,
                                       dias=dias_historicos)
        else:
            print("→ Ya existen ventas, saltando generación histórica.")

        print("\n" + "=" * 60)
        print("✓ INICIALIZACIÓN COMPLETA")
        print("=" * 60)
        print("\nCredenciales de prueba:")
        print("  • admin / admin123          (Administrador)")
        print("  • gerente / gerente123      (Gerente)")
        print("  • trabajador / trabajador123 (Trabajador)")
        print("  • analista / analista123    (Analista)")
        print("\nEjecuta la app con: streamlit run app.py")
    except Exception as e:
        sesion.rollback()
        print(f"\n❌ Error durante la inicialización: {e}")
        raise
    finally:
        sesion.close()


if __name__ == "__main__":
    dias = 90
    if len(sys.argv) > 1:
        try:
            dias = int(sys.argv[1])
        except ValueError:
            pass
    main(dias_historicos=dias)
