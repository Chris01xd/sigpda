from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

from database.conexion import obtener_sesion
from database.modelos import Produccion
from backend.auth import obtener_usuario_actual

router = APIRouter()


class ProduccionCreate(BaseModel):
    id_restaurante: Optional[int] = None
    id_plato: int
    fecha: Optional[date] = None
    cantidad_preparada: int
    cantidad_vendida: int = 0
    cantidad_sobrante: int = 0
    observaciones: Optional[str] = None


def _to_dict(p: Produccion) -> dict:
    return {
        "id_produccion": p.id_produccion,
        "id_restaurante": p.id_restaurante,
        "id_plato": p.id_plato,
        "plato": p.plato.nombre if p.plato else "",
        "id_usuario": p.id_usuario,
        "fecha": p.fecha.isoformat() if p.fecha else None,
        "cantidad_preparada": p.cantidad_preparada,
        "cantidad_vendida": p.cantidad_vendida,
        "cantidad_sobrante": p.cantidad_sobrante,
        "observaciones": p.observaciones,
        "fecha_registro": p.fecha_registro.isoformat() if p.fecha_registro else None,
    }


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        return [_to_dict(p) for p in sesion.query(Produccion).order_by(Produccion.fecha.desc()).all()]
    finally:
        sesion.close()


@router.post("/")
def crear(data: ProduccionCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        p = Produccion(
            id_restaurante=data.id_restaurante,
            id_plato=data.id_plato,
            id_usuario=int(current_user["sub"]),
            fecha=data.fecha or datetime.utcnow().date(),
            cantidad_preparada=data.cantidad_preparada,
            cantidad_vendida=data.cantidad_vendida,
            cantidad_sobrante=data.cantidad_sobrante,
            observaciones=data.observaciones,
        )
        sesion.add(p)
        sesion.commit()
        sesion.refresh(p)
        return _to_dict(p)
    finally:
        sesion.close()


@router.put("/{id}")
def actualizar(id: int, data: ProduccionCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        p = sesion.query(Produccion).filter(Produccion.id_produccion == id).first()
        if not p:
            raise HTTPException(404, "No encontrado")
        p.cantidad_preparada = data.cantidad_preparada
        p.cantidad_vendida = data.cantidad_vendida
        p.cantidad_sobrante = data.cantidad_sobrante
        p.observaciones = data.observaciones
        sesion.commit()
        sesion.refresh(p)
        return _to_dict(p)
    finally:
        sesion.close()


@router.delete("/{id}")
def eliminar(id: int, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        p = sesion.query(Produccion).filter(Produccion.id_produccion == id).first()
        if not p:
            raise HTTPException(404, "No encontrado")
        sesion.delete(p)
        sesion.commit()
        return {"message": "Eliminado"}
    finally:
        sesion.close()
