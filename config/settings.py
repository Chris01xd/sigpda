"""
=================================================================
SIGPDA - Configuración Global del Sistema
=================================================================
Carga variables de entorno y expone constantes utilizadas en
todo el sistema. Soporta PostgreSQL (producción) y SQLite (pruebas).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar archivo .env
RUTA_BASE = Path(__file__).resolve().parent.parent
load_dotenv(RUTA_BASE / ".env")


# ----------------------------------------------------------------
# BASE DE DATOS
# ----------------------------------------------------------------
TIPO_BD = os.getenv("TIPO_BD", "sqlite").lower()

# PostgreSQL
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PUERTO = os.getenv("PG_PUERTO", "5432")
PG_USUARIO = os.getenv("PG_USUARIO", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_BD = os.getenv("PG_BD", "sigpda")

# SQLite
SQLITE_RUTA = os.getenv("SQLITE_RUTA", "database/sigpda.db")


def obtener_url_bd() -> str:
    """Construye la URL de conexión a la base de datos según el tipo."""
    if TIPO_BD == "postgresql":
        return (
            f"postgresql+psycopg2://{PG_USUARIO}:{PG_PASSWORD}"
            f"@{PG_HOST}:{PG_PUERTO}/{PG_BD}"
        )
    # SQLite por defecto
    ruta_absoluta = RUTA_BASE / SQLITE_RUTA
    ruta_absoluta.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{ruta_absoluta}"


# ----------------------------------------------------------------
# n8n / WEBHOOKS
# ----------------------------------------------------------------
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/sigpda")
N8N_HABILITADO = os.getenv("N8N_HABILITADO", "true").lower() == "true"


# ----------------------------------------------------------------
# PARÁMETROS GENERALES
# ----------------------------------------------------------------
NOMBRE_SISTEMA = os.getenv("NOMBRE_SISTEMA", "SIGPDA")
MONEDA = os.getenv("MONEDA", "S/")
UMBRAL_DESPERDICIO_PORCENTAJE = float(os.getenv("UMBRAL_DESPERDICIO_PORCENTAJE", "15"))
ZONA_HORARIA = os.getenv("ZONA_HORARIA", "America/Lima")


# ----------------------------------------------------------------
# SEGURIDAD
# ----------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "llave-defecto-cambiar")
DURACION_SESION_MINUTOS = int(os.getenv("DURACION_SESION_MINUTOS", "480"))


# ----------------------------------------------------------------
# ROLES Y PERMISOS
# ----------------------------------------------------------------
ROLES_DISPONIBLES = ["Administrador", "Gerente", "Trabajador", "Analista"]

PERMISOS_POR_ROL = {
    "Administrador": {
        "todos": ["ver", "crear", "editar", "eliminar", "exportar", "generar_reporte"]
    },
    "Gerente": {
        "usuarios": ["ver"],
        "restaurantes": ["ver", "crear", "editar"],
        "clientes": ["ver", "crear", "editar", "exportar"],
        "proveedores": ["ver", "crear", "editar", "exportar"],
        "platos": ["ver", "crear", "editar"],
        "insumos": ["ver", "crear", "editar"],
        "recetas": ["ver", "crear", "editar"],
        "ventas": ["ver", "crear", "editar", "exportar"],
        "produccion": ["ver", "crear", "editar"],
        "desperdicio": ["ver", "crear", "editar", "exportar"],
        "prediccion": ["ver", "generar_reporte"],
        "dashboard": ["ver"],
        "reportes": ["ver", "generar_reporte", "exportar"],
        "bitacora": ["ver"],
        "configuracion": ["ver", "editar"],
    },
    "Trabajador": {
        "ventas": ["ver", "crear"],
        "produccion": ["ver", "crear"],
        "desperdicio": ["ver", "crear"],
        "insumos": ["ver"],
        "platos": ["ver"],
        "clientes": ["ver"],
        "proveedores": ["ver"],
        "dashboard": ["ver"],
    },
    "Analista": {
        "dashboard": ["ver"],
        "ventas": ["ver", "exportar"],
        "desperdicio": ["ver", "exportar"],
        "clientes": ["ver", "exportar"],
        "proveedores": ["ver", "exportar"],
        "prediccion": ["ver", "generar_reporte"],
        "estadisticas": ["ver", "exportar"],
        "reportes": ["ver", "generar_reporte", "exportar"],
        "bitacora": ["ver"],
    },
}


def usuario_tiene_permiso(rol: str, modulo: str, accion: str) -> bool:
    """Verifica si un rol tiene un permiso específico sobre un módulo."""
    if rol not in PERMISOS_POR_ROL:
        return False
    perms = PERMISOS_POR_ROL[rol]
    if "todos" in perms:
        return accion in perms["todos"]
    if modulo in perms:
        return accion in perms[modulo]
    return False


# ----------------------------------------------------------------
# MOTIVOS DE DESPERDICIO
# ----------------------------------------------------------------
MOTIVOS_DESPERDICIO = [
    "sobreproducción",
    "vencimiento",
    "mala conservación",
    "baja demanda",
    "error operativo",
]


# ----------------------------------------------------------------
# CATEGORÍAS DE PLATOS
# ----------------------------------------------------------------
CATEGORIAS_PLATOS = [
    "Entrada",
    "Plato de fondo",
    "Sopa",
    "Postre",
    "Bebida",
    "Especialidad regional",
    "Combo",
]


# ----------------------------------------------------------------
# UNIDADES DE MEDIDA
# ----------------------------------------------------------------
UNIDADES_MEDIDA = ["kg", "g", "lt", "ml", "unidad", "porción", "atado", "bandeja"]
