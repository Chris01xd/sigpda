from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date

from database.conexion import obtener_sesion
from database.modelos import Insumo
from backend.auth import obtener_usuario_actual

router = APIRouter()


class InsumoCreate(BaseModel):
    id_restaurante: Optional[int] = None
    id_proveedor: Optional[int] = None
    nombre: str
    categoria: Optional[str] = None
    unidad_medida: str
    stock_disponible: float = 0
    stock_minimo: float = 0
    costo_unitario: float = 0
    fecha_vencimiento: Optional[date] = None
    proveedor: Optional[str] = None
    estado: bool = True


def _to_dict(i: Insumo) -> dict:
    return {
        "id_insumo": i.id_insumo,
        "id_restaurante": i.id_restaurante,
        "id_proveedor": i.id_proveedor,
        "nombre": i.nombre,
        "categoria": i.categoria,
        "unidad_medida": i.unidad_medida,
        "stock_disponible": float(i.stock_disponible) if i.stock_disponible else 0,
        "stock_minimo": float(i.stock_minimo) if i.stock_minimo else 0,
        "costo_unitario": float(i.costo_unitario) if i.costo_unitario else 0,
        "fecha_vencimiento": i.fecha_vencimiento.isoformat() if i.fecha_vencimiento else None,
        "proveedor": i.proveedor,
        "estado": i.estado,
        "stock_critico": float(i.stock_disponible or 0) <= float(i.stock_minimo or 0),
        "fecha_creacion": i.fecha_creacion.isoformat() if i.fecha_creacion else None,
    }


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        return [_to_dict(i) for i in sesion.query(Insumo).filter(Insumo.estado == True).all()]
    finally:
        sesion.close()


@router.post("/")
def crear(data: InsumoCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        i = Insumo(**data.dict())
        sesion.add(i)
        sesion.commit()
        sesion.refresh(i)
        return _to_dict(i)
    finally:
        sesion.close()


@router.put("/{id}")
def actualizar(id: int, data: InsumoCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        i = sesion.query(Insumo).filter(Insumo.id_insumo == id).first()
        if not i:
            raise HTTPException(404, "No encontrado")
        for k, v in data.dict().items():
            setattr(i, k, v)
        sesion.commit()
        sesion.refresh(i)
        return _to_dict(i)
    finally:
        sesion.close()


@router.delete("/{id}")
def eliminar(id: int, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        i = sesion.query(Insumo).filter(Insumo.id_insumo == id).first()
        if not i:
            raise HTTPException(404, "No encontrado")
        i.estado = False
        sesion.commit()
        return {"message": "Eliminado"}
    finally:
        sesion.close()
