from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from database.conexion import obtener_sesion
from database.modelos import Restaurante
from backend.auth import obtener_usuario_actual

router = APIRouter()


class RestauranteCreate(BaseModel):
    nombre_comercial: str
    ruc: Optional[str] = None
    direccion: Optional[str] = None
    distrito: Optional[str] = None
    provincia: Optional[str] = None
    responsable: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    estado: bool = True


def _to_dict(r: Restaurante) -> dict:
    return {
        "id_restaurante": r.id_restaurante,
        "nombre_comercial": r.nombre_comercial,
        "ruc": r.ruc,
        "direccion": r.direccion,
        "distrito": r.distrito,
        "provincia": r.provincia,
        "responsable": r.responsable,
        "telefono": r.telefono,
        "correo": r.correo,
        "estado": r.estado,
        "fecha_registro": r.fecha_registro.isoformat() if r.fecha_registro else None,
    }


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        return [_to_dict(r) for r in sesion.query(Restaurante).all()]
    finally:
        sesion.close()


@router.post("/")
def crear(data: RestauranteCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        r = Restaurante(**data.dict())
        sesion.add(r)
        sesion.commit()
        sesion.refresh(r)
        return _to_dict(r)
    finally:
        sesion.close()


@router.put("/{id}")
def actualizar(id: int, data: RestauranteCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        r = sesion.query(Restaurante).filter(Restaurante.id_restaurante == id).first()
        if not r:
            raise HTTPException(404, "No encontrado")
        for k, v in data.dict().items():
            setattr(r, k, v)
        sesion.commit()
        sesion.refresh(r)
        return _to_dict(r)
    finally:
        sesion.close()


@router.delete("/{id}")
def eliminar(id: int, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        r = sesion.query(Restaurante).filter(Restaurante.id_restaurante == id).first()
        if not r:
            raise HTTPException(404, "No encontrado")
        r.estado = False
        sesion.commit()
        return {"message": "Eliminado"}
    finally:
        sesion.close()
