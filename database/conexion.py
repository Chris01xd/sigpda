"""
=================================================================
SIGPDA - Conexión a la Base de Datos
=================================================================
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config.settings import obtener_url_bd, TIPO_BD
from database.modelos import Base


# Engine SQLAlchemy (singleton)
_url = obtener_url_bd()
_kwargs = {"echo": False, "future": True}
if TIPO_BD == "sqlite":
    _kwargs["connect_args"] = {"check_same_thread": False}

motor = create_engine(_url, **_kwargs)
SessionLocal = scoped_session(sessionmaker(bind=motor, autocommit=False, autoflush=False))


def crear_tablas():
    """Crea todas las tablas si no existen y aplica migraciones incrementales."""
    Base.metadata.create_all(motor)
    _aplicar_migraciones()


def _aplicar_migraciones():
    """Agrega columnas nuevas a tablas existentes sin perder datos."""
    from sqlalchemy import text
    migraciones = {
        "ventas": [
            ("id_cliente",         "INTEGER"),
            ("tipo_comprobante",   'VARCHAR(20) DEFAULT "ticket"'),
            ("numero_comprobante", "VARCHAR(20)"),
            ("cliente_nombre",     "VARCHAR(150)"),
            ("cliente_documento",  "VARCHAR(15)"),
        ],
        "insumos": [
            ("id_proveedor", "INTEGER"),
        ],
    }
    with motor.connect() as conn:
        for tabla, columnas in migraciones.items():
            try:
                result = conn.execute(text(f"PRAGMA table_info({tabla})"))
                existentes = {r[1] for r in result.fetchall()}
                for col, tipo in columnas:
                    if col not in existentes:
                        conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}"))
                conn.commit()
            except Exception:
                pass


def obtener_sesion():
    """Devuelve una nueva sesión SQLAlchemy."""
    return SessionLocal()


def cerrar_sesiones():
    SessionLocal.remove()
