from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

from database.conexion import obtener_sesion
from database.modelos import Venta, DetalleVenta, Plato
from backend.auth import obtener_usuario_actual

router = APIRouter()


class DetalleCreate(BaseModel):
    id_plato: int
    cantidad: int
    precio_unitario: float


class VentaCreate(BaseModel):
    id_restaurante: Optional[int] = None
    id_cliente: Optional[int] = None
    fecha: Optional[date] = None
    metodo_pago: str = "efectivo"
    tipo_comprobante: str = "ticket"
    numero_comprobante: Optional[str] = None
    cliente_nombre: Optional[str] = None
    cliente_documento: Optional[str] = None
    observaciones: Optional[str] = None
    detalles: List[DetalleCreate]


def _detalle_dict(d: DetalleVenta) -> dict:
    return {
        "id_detalle": d.id_detalle,
        "id_plato": d.id_plato,
        "plato": d.plato.nombre if d.plato else "",
        "cantidad": d.cantidad,
        "precio_unitario": float(d.precio_unitario),
        "subtotal": float(d.subtotal),
    }


def _venta_dict(v: Venta) -> dict:
    return {
        "id_venta": v.id_venta,
        "id_restaurante": v.id_restaurante,
        "id_usuario": v.id_usuario,
        "id_cliente": v.id_cliente,
        "fecha": v.fecha.isoformat() if v.fecha else None,
        "hora": v.hora,
        "total": float(v.total) if v.total else 0,
        "metodo_pago": v.metodo_pago,
        "tipo_comprobante": v.tipo_comprobante,
        "numero_comprobante": v.numero_comprobante,
        "cliente_nombre": v.cliente_nombre,
        "cliente_documento": v.cliente_documento,
        "observaciones": v.observaciones,
        "fecha_registro": v.fecha_registro.isoformat() if v.fecha_registro else None,
        "detalles": [_detalle_dict(d) for d in v.detalles],
    }


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        ventas = sesion.query(Venta).order_by(Venta.fecha_registro.desc()).limit(200).all()
        return [_venta_dict(v) for v in ventas]
    finally:
        sesion.close()


@router.get("/{id}")
def obtener(id: int, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        v = sesion.query(Venta).filter(Venta.id_venta == id).first()
        if not v:
            raise HTTPException(404, "No encontrado")
        return _venta_dict(v)
    finally:
        sesion.close()


@router.post("/")
def crear(data: VentaCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        ahora = datetime.utcnow()
        total = sum(d.precio_unitario * d.cantidad for d in data.detalles)

        v = Venta(
            id_restaurante=data.id_restaurante,
            id_usuario=int(current_user["sub"]),
            id_cliente=data.id_cliente,
            fecha=data.fecha or ahora.date(),
            hora=ahora.strftime("%H:%M:%S"),
            total=total,
            metodo_pago=data.metodo_pago,
            tipo_comprobante=data.tipo_comprobante,
            numero_comprobante=data.numero_comprobante,
            cliente_nombre=data.cliente_nombre,
            cliente_documento=data.cliente_documento,
            observaciones=data.observaciones,
        )
        sesion.add(v)
        sesion.flush()

        for det in data.detalles:
            d = DetalleVenta(
                id_venta=v.id_venta,
                id_plato=det.id_plato,
                cantidad=det.cantidad,
                precio_unitario=det.precio_unitario,
                subtotal=det.precio_unitario * det.cantidad,
            )
            sesion.add(d)

        sesion.commit()
        sesion.refresh(v)
        return _venta_dict(v)
    finally:
        sesion.close()


@router.delete("/{id}")
def eliminar(id: int, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        v = sesion.query(Venta).filter(Venta.id_venta == id).first()
        if not v:
            raise HTTPException(404, "No encontrado")
        sesion.delete(v)
        sesion.commit()
        return {"message": "Eliminado"}
    finally:
        sesion.close()
