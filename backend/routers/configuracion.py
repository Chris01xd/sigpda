from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database.conexion import obtener_sesion
from database.modelos import Configuracion
from backend.auth import obtener_usuario_actual
from backend.services.notificaciones import probar_email, probar_whatsapp

router = APIRouter()


class ConfigUpdate(BaseModel):
    clave: str
    valor: str
    descripcion: Optional[str] = None


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        return [
            {
                "id_configuracion": c.id_configuracion,
                "clave": c.clave,
                "valor": c.valor,
                "descripcion": c.descripcion,
                "fecha_actualizacion": c.fecha_actualizacion.isoformat() if c.fecha_actualizacion else None,
            }
            for c in sesion.query(Configuracion).all()
        ]
    finally:
        sesion.close()


@router.post("/probar-email")
def probar_email_endpoint(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        rows = sesion.query(Configuracion).filter(
            Configuracion.clave.in_(["notif_email_destino", "notif_email_remitente", "notif_email_password"])
        ).all()
        cfg = {r.clave: (r.valor or "").strip() for r in rows}
    finally:
        sesion.close()

    destino = cfg.get("notif_email_destino", "")
    remitente = cfg.get("notif_email_remitente", "")
    password = cfg.get("notif_email_password", "")
    if not (destino and remitente and password):
        return {"ok": False, "mensaje": "Faltan datos: destino, remitente o contraseña de aplicación."}
    return probar_email(destino, remitente, password)


@router.post("/probar-whatsapp")
def probar_whatsapp_endpoint(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        rows = sesion.query(Configuracion).filter(
            Configuracion.clave.in_(["notif_telefono", "notif_twilio_sid", "notif_twilio_token", "notif_twilio_numero"])
        ).all()
        cfg = {r.clave: (r.valor or "").strip() for r in rows}
    finally:
        sesion.close()

    telefono       = cfg.get("notif_telefono", "")
    sid            = cfg.get("notif_twilio_sid", "")
    token          = cfg.get("notif_twilio_token", "")
    numero_twilio  = cfg.get("notif_twilio_numero", "")
    if not (telefono and sid and token and numero_twilio):
        return {"ok": False, "mensaje": "Faltan datos: teléfono, SID, token o número Twilio."}
    return probar_whatsapp(telefono, sid, token, numero_twilio)


@router.put("/")
def actualizar(data: ConfigUpdate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        c = sesion.query(Configuracion).filter(Configuracion.clave == data.clave).first()
        if c:
            c.valor = data.valor
            if data.descripcion:
                c.descripcion = data.descripcion
            c.fecha_actualizacion = datetime.utcnow()
        else:
            c = Configuracion(clave=data.clave, valor=data.valor, descripcion=data.descripcion)
            sesion.add(c)
        sesion.commit()
        return {"message": "Actualizado"}
    finally:
        sesion.close()
