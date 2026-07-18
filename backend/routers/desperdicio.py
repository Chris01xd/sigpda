from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

from database.conexion import obtener_sesion
from database.modelos import Desperdicio
from backend.auth import obtener_usuario_actual

router = APIRouter()


class DesperdicioCreate(BaseModel):
    id_restaurante: Optional[int] = None
    id_plato: Optional[int] = None
    id_insumo: Optional[int] = None
    fecha: Optional[date] = None
    tipo: str  # plato / insumo
    cantidad: float
    unidad_medida: str
    motivo: str
    costo_estimado: float = 0
    observaciones: Optional[str] = None


def _to_dict(d: Desperdicio) -> dict:
    return {
        "id_desperdicio": d.id_desperdicio,
        "id_restaurante": d.id_restaurante,
        "id_plato": d.id_plato,
        "plato": d.plato.nombre if d.plato else None,
        "id_insumo": d.id_insumo,
        "insumo": d.insumo.nombre if d.insumo else None,
        "id_usuario": d.id_usuario,
        "fecha": d.fecha.isoformat() if d.fecha else None,
        "tipo": d.tipo,
        "cantidad": float(d.cantidad),
        "unidad_medida": d.unidad_medida,
        "motivo": d.motivo,
        "costo_estimado": float(d.costo_estimado) if d.costo_estimado else 0,
        "observaciones": d.observaciones,
        "fecha_registro": d.fecha_registro.isoformat() if d.fecha_registro else None,
    }


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        return [_to_dict(d) for d in sesion.query(Desperdicio).order_by(Desperdicio.fecha.desc()).all()]
    finally:
        sesion.close()


@router.post("/")
def crear(data: DesperdicioCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        d = Desperdicio(
            id_restaurante=data.id_restaurante,
            id_plato=data.id_plato,
            id_insumo=data.id_insumo,
            id_usuario=int(current_user["sub"]),
            fecha=data.fecha or datetime.utcnow().date(),
            tipo=data.tipo,
            cantidad=data.cantidad,
            unidad_medida=data.unidad_medida,
            motivo=data.motivo,
            costo_estimado=data.costo_estimado,
            observaciones=data.observaciones,
        )
        sesion.add(d)
        sesion.commit()
        sesion.refresh(d)
        return _to_dict(d)
    finally:
        sesion.close()


@router.delete("/{id}")
def eliminar(id: int, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        d = sesion.query(Desperdicio).filter(Desperdicio.id_desperdicio == id).first()
        if not d:
            raise HTTPException(404, "No encontrado")
        sesion.delete(d)
        sesion.commit()
        return {"message": "Eliminado"}
    finally:
        sesion.close()
