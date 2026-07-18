from fastapi import APIRouter, Depends
from datetime import date, timedelta
from sqlalchemy import func

from database.conexion import obtener_sesion
from database.modelos import Insumo, Desperdicio, Produccion, Plato, DetalleVenta, Venta
from backend.auth import obtener_usuario_actual
from config.settings import UMBRAL_DESPERDICIO_PORCENTAJE

router = APIRouter()


@router.get("/")
def obtener(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        recomendaciones = []
        hoy = date.today()
        hace_30 = hoy - timedelta(days=30)
        en_7_dias = hoy + timedelta(days=7)

        # 1. Insumos con stock crítico
        criticos = sesion.query(Insumo).filter(
            Insumo.estado == True,
            Insumo.stock_disponible <= Insumo.stock_minimo,
        ).all()
        for i in criticos:
            recomendaciones.append({
                "tipo": "stock_bajo",
                "severidad": "alta",
                "titulo": f"Reponer {i.nombre}",
                "descripcion": f"Stock actual {float(i.stock_disponible or 0)} {i.unidad_medida} es menor al mínimo ({float(i.stock_minimo or 0)} {i.unidad_medida}). Solicitar reposición urgente.",
                "modulo": "insumos",
            })

        # 2. Insumos próximos a vencer
        por_vencer = sesion.query(Insumo).filter(
            Insumo.estado == True,
            Insumo.fecha_vencimiento != None,
            Insumo.fecha_vencimiento <= en_7_dias,
            Insumo.fecha_vencimiento >= hoy,
        ).all()
        for i in por_vencer:
            dias = (i.fecha_vencimiento - hoy).days
            recomendaciones.append({
                "tipo": "vencimiento",
                "severidad": "alta" if dias <= 2 else "media",
                "titulo": f"Usar pronto: {i.nombre}",
                "descripcion": f"Vence en {dias} día(s) ({i.fecha_vencimiento}). Priorizar su uso en producción.",
                "modulo": "insumos",
            })

        # 3. Platos con alta producción sobrante (desperdicio de producción)
        sobrantes = sesion.query(
            Plato.nombre,
            func.sum(Produccion.cantidad_sobrante).label("sobrante"),
            func.sum(Produccion.cantidad_preparada).label("preparado"),
        ).join(Produccion, Plato.id_plato == Produccion.id_plato)\
         .filter(Produccion.fecha >= hace_30)\
         .group_by(Plato.id_plato, Plato.nombre)\
         .having(func.sum(Produccion.cantidad_preparada) > 0).all()

        for s in sobrantes:
            pct = (float(s.sobrante or 0) / float(s.preparado or 1)) * 100
            if pct > UMBRAL_DESPERDICIO_PORCENTAJE:
                recomendaciones.append({
                    "tipo": "sobreproduccion",
                    "severidad": "media",
                    "titulo": f"Reducir producción de {s.nombre}",
                    "descripcion": f"El {pct:.1f}% de la producción de {s.nombre} se desperdicia. Reducir cantidad preparada diaria.",
                    "modulo": "produccion",
                })

        # 4. Motivos de desperdicio frecuentes
        top_motivos = sesion.query(
            Desperdicio.motivo,
            func.count(Desperdicio.id_desperdicio).label("frecuencia"),
            func.sum(Desperdicio.costo_estimado).label("costo"),
        ).filter(Desperdicio.fecha >= hace_30)\
         .group_by(Desperdicio.motivo)\
         .order_by(func.count(Desperdicio.id_desperdicio).desc())\
         .limit(3).all()

        for m in top_motivos:
            if float(m.costo or 0) > 0:
                recomendaciones.append({
                    "tipo": "motivo_desperdicio",
                    "severidad": "baja",
                    "titulo": f"Motivo frecuente: {m.motivo}",
                    "descripcion": f"En los últimos 30 días ocurrió {int(m.frecuencia)} veces con costo de S/ {float(m.costo or 0):.2f}. Implementar plan de mejora.",
                    "modulo": "desperdicio",
                })

        return recomendaciones
    finally:
        sesion.close()
