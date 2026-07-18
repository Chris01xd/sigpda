from fastapi import APIRouter, Depends
from datetime import date, timedelta
from sqlalchemy import func

from database.conexion import obtener_sesion
from database.modelos import Venta, DetalleVenta, Desperdicio, Produccion, Plato
from backend.auth import obtener_usuario_actual

router = APIRouter()


@router.get("/resumen")
def resumen(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        inicio_anio = hoy.replace(month=1, day=1)

        total_ventas_mes = float(sesion.query(func.coalesce(func.sum(Venta.total), 0)).filter(
            Venta.fecha >= inicio_mes
        ).scalar() or 0)

        total_ventas_anio = float(sesion.query(func.coalesce(func.sum(Venta.total), 0)).filter(
            Venta.fecha >= inicio_anio
        ).scalar() or 0)

        total_desperdicio_mes = float(sesion.query(func.coalesce(func.sum(Desperdicio.costo_estimado), 0)).filter(
            Desperdicio.fecha >= inicio_mes
        ).scalar() or 0)

        num_ventas_mes = int(sesion.query(func.count(Venta.id_venta)).filter(
            Venta.fecha >= inicio_mes
        ).scalar() or 0)

        sobrante_mes = int(sesion.query(func.coalesce(func.sum(Produccion.cantidad_sobrante), 0)).filter(
            Produccion.fecha >= inicio_mes
        ).scalar() or 0)

        return {
            "total_ventas_mes": total_ventas_mes,
            "total_ventas_anio": total_ventas_anio,
            "total_desperdicio_mes": total_desperdicio_mes,
            "num_ventas_mes": num_ventas_mes,
            "sobrante_mes": sobrante_mes,
        }
    finally:
        sesion.close()


@router.get("/ventas-por-mes")
def ventas_por_mes(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        hace_12_meses = date.today() - timedelta(days=365)
        filas = sesion.query(
            func.strftime("%Y-%m", Venta.fecha).label("mes"),
            func.sum(Venta.total).label("total"),
            func.count(Venta.id_venta).label("num"),
        ).filter(Venta.fecha >= hace_12_meses)\
         .group_by(func.strftime("%Y-%m", Venta.fecha))\
         .order_by(func.strftime("%Y-%m", Venta.fecha)).all()

        return [{"mes": f.mes, "total": float(f.total or 0), "num": int(f.num)} for f in filas]
    finally:
        sesion.close()


@router.get("/desperdicio-por-mes")
def desperdicio_por_mes(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        hace_12_meses = date.today() - timedelta(days=365)
        filas = sesion.query(
            func.strftime("%Y-%m", Desperdicio.fecha).label("mes"),
            func.sum(Desperdicio.costo_estimado).label("costo"),
            func.count(Desperdicio.id_desperdicio).label("num"),
        ).filter(Desperdicio.fecha >= hace_12_meses)\
         .group_by(func.strftime("%Y-%m", Desperdicio.fecha))\
         .order_by(func.strftime("%Y-%m", Desperdicio.fecha)).all()

        return [{"mes": f.mes, "costo": float(f.costo or 0), "num": int(f.num)} for f in filas]
    finally:
        sesion.close()
