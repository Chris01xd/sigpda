from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from database.conexion import obtener_sesion
from database.modelos import Receta, Plato, Insumo
from backend.auth import obtener_usuario_actual

router = APIRouter()


class RecetaCreate(BaseModel):
    id_plato: int
    id_insumo: int
    cantidad_usada: float
    unidad_medida: Optional[str] = None


def _to_dict(r: Receta) -> dict:
    return {
        "id_receta": r.id_receta,
        "id_plato": r.id_plato,
        "plato": r.plato.nombre if r.plato else "",
        "id_insumo": r.id_insumo,
        "insumo": r.insumo.nombre if r.insumo else "",
        "cantidad_usada": float(r.cantidad_usada) if r.cantidad_usada else 0,
        "unidad_medida": r.unidad_medida,
        "fecha_creacion": r.fecha_creacion.isoformat() if r.fecha_creacion else None,
    }


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        return [_to_dict(r) for r in sesion.query(Receta).all()]
    finally:
        sesion.close()


@router.get("/plato/{id_plato}")
def por_plato(id_plato: int, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        return [_to_dict(r) for r in sesion.query(Receta).filter(Receta.id_plato == id_plato).all()]
    finally:
        sesion.close()


@router.post("/")
def crear(data: RecetaCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        r = Receta(**data.dict())
        sesion.add(r)
        sesion.commit()
        sesion.refresh(r)
        return _to_dict(r)
    finally:
        sesion.close()


@router.delete("/{id}")
def eliminar(id: int, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        r = sesion.query(Receta).filter(Receta.id_receta == id).first()
        if not r:
            raise HTTPException(404, "No encontrado")
        sesion.delete(r)
        sesion.commit()
        return {"message": "Eliminado"}
    finally:
        sesion.close()
