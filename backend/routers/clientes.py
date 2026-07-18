from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from database.conexion import obtener_sesion
from database.modelos import Cliente
from backend.auth import obtener_usuario_actual

router = APIRouter()


class ClienteCreate(BaseModel):
    id_restaurante: Optional[int] = None
    nombre: str
    tipo_documento: str = "DNI"
    numero_documento: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    estado: bool = True


def _to_dict(c: Cliente) -> dict:
    return {
        "id_cliente": c.id_cliente,
        "id_restaurante": c.id_restaurante,
        "nombre": c.nombre,
        "tipo_documento": c.tipo_documento,
        "numero_documento": c.numero_documento,
        "direccion": c.direccion,
        "telefono": c.telefono,
        "correo": c.correo,
        "estado": c.estado,
        "fecha_creacion": c.fecha_creacion.isoformat() if c.fecha_creacion else None,
    }


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        return [_to_dict(c) for c in sesion.query(Cliente).filter(Cliente.estado == True).all()]
    finally:
        sesion.close()


@router.post("/")
def crear(data: ClienteCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        existente = sesion.query(Cliente).filter(Cliente.numero_documento == data.numero_documento).first()
        if existente:
            raise HTTPException(400, "Documento ya registrado")
        c = Cliente(**data.dict())
        sesion.add(c)
        sesion.commit()
        sesion.refresh(c)
        return _to_dict(c)
    finally:
        sesion.close()


@router.put("/{id}")
def actualizar(id: int, data: ClienteCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        c = sesion.query(Cliente).filter(Cliente.id_cliente == id).first()
        if not c:
            raise HTTPException(404, "No encontrado")
        for k, v in data.dict().items():
            setattr(c, k, v)
        sesion.commit()
        sesion.refresh(c)
        return _to_dict(c)
    finally:
        sesion.close()


@router.delete("/{id}")
def eliminar(id: int, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        c = sesion.query(Cliente).filter(Cliente.id_cliente == id).first()
        if not c:
            raise HTTPException(404, "No encontrado")
        c.estado = False
        sesion.commit()
        return {"message": "Eliminado"}
    finally:
        sesion.close()
