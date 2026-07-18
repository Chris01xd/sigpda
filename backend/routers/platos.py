from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

from database.conexion import obtener_sesion
from database.modelos import Plato
from backend.auth import obtener_usuario_actual

router = APIRouter()


class PlatoCreate(BaseModel):
    id_restaurante: Optional[int] = None
    nombre: str
    categoria: Optional[str] = None
    descripcion: Optional[str] = None
    precio_venta: float
    costo_estimado: float = 0
    tiempo_preparacion_min: int = 0
    estado: bool = True


def _to_dict(p: Plato) -> dict:
    return {
        "id_plato": p.id_plato,
        "id_restaurante": p.id_restaurante,
        "nombre": p.nombre,
        "categoria": p.categoria,
        "descripcion": p.descripcion,
        "precio_venta": float(p.precio_venta) if p.precio_venta else 0,
        "costo_estimado": float(p.costo_estimado) if p.costo_estimado else 0,
        "tiempo_preparacion_min": p.tiempo_preparacion_min,
        "estado": p.estado,
        "fecha_creacion": p.fecha_creacion.isoformat() if p.fecha_creacion else None,
    }


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        return [_to_dict(p) for p in sesion.query(Plato).filter(Plato.estado == True).all()]
    finally:
        sesion.close()


@router.post("/")
def crear(data: PlatoCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        p = Plato(**data.dict())
        sesion.add(p)
        sesion.commit()
        sesion.refresh(p)
        return _to_dict(p)
    finally:
        sesion.close()


@router.put("/{id}")
def actualizar(id: int, data: PlatoCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        p = sesion.query(Plato).filter(Plato.id_plato == id).first()
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
        p = sesion.query(Plato).filter(Plato.id_plato == id).first()
        if not p:
            raise HTTPException(404, "No encontrado")
        p.estado = False
        sesion.commit()
        return {"message": "Eliminado"}
    finally:
        sesion.close()
