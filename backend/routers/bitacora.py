from fastapi import APIRouter, Depends
from typing import Optional

from database.conexion import obtener_sesion
from database.modelos import Bitacora
from backend.auth import obtener_usuario_actual

router = APIRouter()


def _to_dict(b: Bitacora) -> dict:
    return {
        "id_bitacora": b.id_bitacora,
        "id_usuario": b.id_usuario,
        "usuario_nombre": b.usuario_nombre,
        "rol": b.rol,
        "modulo": b.modulo,
        "accion": b.accion,
        "descripcion": b.descripcion,
        "fecha": b.fecha.isoformat() if b.fecha else None,
        "hora": b.hora,
        "ip_equipo": b.ip_equipo,
        "resultado": b.resultado,
    }


@router.get("/")
def listar(
    modulo: Optional[str] = None,
    resultado: Optional[str] = None,
    limit: int = 200,
    current_user: dict = Depends(obtener_usuario_actual),
):
    sesion = obtener_sesion()
    try:
        q = sesion.query(Bitacora).order_by(Bitacora.id_bitacora.desc())
        if modulo:
            q = q.filter(Bitacora.modulo == modulo)
        if resultado:
            q = q.filter(Bitacora.resultado == resultado)
        return [_to_dict(b) for b in q.limit(limit).all()]
    finally:
        sesion.close()
