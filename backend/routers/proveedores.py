from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from database.conexion import obtener_sesion
from database.modelos import Proveedor
from backend.auth import obtener_usuario_actual

router = APIRouter()


class ProveedorCreate(BaseModel):
    nombre: str
    tipo_documento: str = "RUC"
    numero_documento: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    estado: bool = True


def _to_dict(p: Proveedor) -> dict:
    return {
        "id_proveedor": p.id_proveedor,
        "nombre": p.nombre,
        "tipo_documento": p.tipo_documento,
        "numero_documento": p.numero_documento,
        "contacto": p.contacto,
        "telefono": p.telefono,
        "correo": p.correo,
        "direccion": p.direccion,
        "estado": p.estado,
        "fecha_creacion": p.fecha_creacion.isoformat() if p.fecha_creacion else None,
    }


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        return [_to_dict(p) for p in sesion.query(Proveedor).filter(Proveedor.estado == True).all()]
    finally:
        sesion.close()


@router.post("/")
def crear(data: ProveedorCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        p = Proveedor(**data.dict())
        sesion.add(p)
        sesion.commit()
        sesion.refresh(p)
        return _to_dict(p)
    finally:
        sesion.close()


@router.put("/{id}")
def actualizar(id: int, data: ProveedorCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        p = sesion.query(Proveedor).filter(Proveedor.id_proveedor == id).first()
        if not p:
            raise HTTPException(404, "No encontrado")
        for k, v in data.dict().items():
            setattr(p, k, v)
        sesion.commit()
        sesion.refresh(p)
        return _to_dict(p)
    finally:
        sesion.close()


@router.delete("/{id}")
def eliminar(id: int, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        p = sesion.query(Proveedor).filter(Proveedor.id_proveedor == id).first()
        if not p:
            raise HTTPException(404, "No encontrado")
        p.estado = False
        sesion.commit()
        return {"message": "Eliminado"}
    finally:
        sesion.close()
