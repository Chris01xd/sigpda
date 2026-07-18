import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.conexion import crear_tablas

from backend.routers import (
    auth, usuarios, roles, restaurantes, clientes,
    proveedores, platos, insumos, recetas, ventas,
    produccion, desperdicio, dashboard, estadisticas,
    bitacora, configuracion, recomendaciones, ia_prediccion,
    alertas_inteligentes, sostenibilidad, reportes,
)

app = FastAPI(
    title="SIGPDA API",
    description="Sistema Inteligente de Gestión y Predicción de Desperdicio Alimentario",
    version="2.0.0",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(usuarios.router, prefix="/api/usuarios", tags=["Usuarios"])
app.include_router(roles.router, prefix="/api/roles", tags=["Roles"])
app.include_router(restaurantes.router, prefix="/api/restaurantes", tags=["Restaurantes"])
app.include_router(clientes.router, prefix="/api/clientes", tags=["Clientes"])
app.include_router(proveedores.router, prefix="/api/proveedores", tags=["Proveedores"])
app.include_router(platos.router, prefix="/api/platos", tags=["Platos"])
app.include_router(insumos.router, prefix="/api/insumos", tags=["Insumos"])
app.include_router(recetas.router, prefix="/api/recetas", tags=["Recetas"])
app.include_router(ventas.router, prefix="/api/ventas", tags=["Ventas"])
app.include_router(produccion.router, prefix="/api/produccion", tags=["Producción"])
app.include_router(desperdicio.router, prefix="/api/desperdicio", tags=["Desperdicio"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(estadisticas.router, prefix="/api/estadisticas", tags=["Estadísticas"])
app.include_router(bitacora.router, prefix="/api/bitacora", tags=["Bitácora"])
app.include_router(configuracion.router, prefix="/api/configuracion", tags=["Configuración"])
app.include_router(recomendaciones.router, prefix="/api/recomendaciones", tags=["Recomendaciones"])
app.include_router(ia_prediccion.router, prefix="/api/ia", tags=["IA"])
app.include_router(alertas_inteligentes.router, prefix="/api/alertas-inteligentes", tags=["Alertas Inteligentes"])
app.include_router(sostenibilidad.router,       prefix="/api/sostenibilidad",       tags=["Sostenibilidad"])
app.include_router(reportes.router,             prefix="/api/reportes",             tags=["Reportes"])


_NOTIF_SEED = [
    ("notif_email_activa",     "false",  "Habilitar envío de alertas por correo electrónico (true/false)"),
    ("notif_email_destino",    "",       "Dirección de correo que recibirá las alertas"),
    ("notif_email_remitente",  "",       "Cuenta Gmail remitente (ej: sigpda@gmail.com)"),
    ("notif_email_password",   "",       "Contraseña de aplicación Gmail (16 caracteres)"),
    ("notif_whatsapp_activa",  "false",  "Habilitar envío de alertas por WhatsApp vía Twilio (true/false)"),
    ("notif_telefono",         "",       "Número destino WhatsApp con código de país (ej: +51999888777)"),
    ("notif_twilio_sid",       "",       "Account SID de Twilio"),
    ("notif_twilio_token",     "",       "Auth Token de Twilio"),
    ("notif_twilio_numero",    "",       "Número Twilio habilitado para WhatsApp (ej: +14155238886)"),
]


@app.on_event("startup")
def startup():
    crear_tablas()
    _seed_notificaciones()


def _seed_notificaciones():
    from database.conexion import obtener_sesion
    from database.modelos import Configuracion
    sesion = obtener_sesion()
    try:
        for clave, valor_defecto, descripcion in _NOTIF_SEED:
            existe = sesion.query(Configuracion).filter(Configuracion.clave == clave).first()
            if not existe:
                sesion.add(Configuracion(clave=clave, valor=valor_defecto, descripcion=descripcion))
        sesion.commit()
    except Exception:
        sesion.rollback()
    finally:
        sesion.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
