from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from database.conexion import obtener_sesion
from database.modelos import Rol, Permiso
from backend.auth import obtener_usuario_actual

router = APIRouter()


class RolCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    estado: bool = True


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        roles = sesion.query(Rol).filter(Rol.estado == True).all()
        return [
            {
                "id_rol": r.id_rol,
                "nombre": r.nombre,
                "descripcion": r.descripcion,
                "estado": r.estado,
                "fecha_creacion": r.fecha_creacion.isoformat() if r.fecha_creacion else None,
            }
            for r in roles
        ]
    finally:
        sesion.close()


@router.post("/")
def crear(data: RolCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        r = Rol(nombre=data.nombre, descripcion=data.descripcion, estado=data.estado)
        sesion.add(r)
        sesion.commit()
        sesion.refresh(r)
        return {"id_rol": r.id_rol, "nombre": r.nombre}
    finally:
        sesion.close()
