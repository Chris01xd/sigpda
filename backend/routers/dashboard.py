from fastapi import APIRouter, Depends
from datetime import date, datetime, timedelta
from sqlalchemy import func

from database.conexion import obtener_sesion
from database.modelos import Venta, DetalleVenta, Desperdicio, Insumo, Plato, Produccion, AlertaInteligente, Receta
from backend.auth import obtener_usuario_actual

router = APIRouter()


@router.get("/kpis")
def kpis(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)

        ventas_mes = sesion.query(func.coalesce(func.sum(Venta.total), 0)).filter(
            Venta.fecha >= inicio_mes
        ).scalar() or 0

        num_ventas_hoy = sesion.query(func.count(Venta.id_venta)).filter(
            Venta.fecha == hoy
        ).scalar() or 0

        costo_desperdicio_mes = sesion.query(func.coalesce(func.sum(Desperdicio.costo_estimado), 0)).filter(
            Desperdicio.fecha >= inicio_mes
        ).scalar() or 0

        stock_critico = sesion.query(func.count(Insumo.id_insumo)).filter(
            Insumo.estado == True,
            Insumo.stock_disponible <= Insumo.stock_minimo,
        ).scalar() or 0

        alertas_criticas = sesion.query(func.count(AlertaInteligente.id_alerta)).filter(
            AlertaInteligente.nivel_riesgo.in_(["ALTO", "CRITICO"]),
            AlertaInteligente.estado == "pendiente",
        ).scalar() or 0

        return {
            "ventas_mes": float(ventas_mes),
            "num_ventas_hoy": int(num_ventas_hoy),
            "costo_desperdicio_mes": float(costo_desperdicio_mes),
            "stock_critico": int(stock_critico),
            "alertas_criticas": int(alertas_criticas),
        }
    finally:
        sesion.close()


@router.get("/ventas-recientes")
def ventas_recientes(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        hace_30 = date.today() - timedelta(days=30)
        filas = sesion.query(
            Venta.fecha,
            func.sum(Venta.total).label("total"),
            func.count(Venta.id_venta).label("num_ventas"),
        ).filter(Venta.fecha >= hace_30).group_by(Venta.fecha).order_by(Venta.fecha).all()

        return [
            {"fecha": str(f.fecha), "total": float(f.total), "num_ventas": int(f.num_ventas)}
            for f in filas
        ]
    finally:
        sesion.close()


@router.get("/desperdicio-por-motivo")
def desperdicio_motivos(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        hace_30 = date.today() - timedelta(days=30)
        filas = sesion.query(
            Desperdicio.motivo,
            func.sum(Desperdicio.costo_estimado).label("costo"),
            func.count(Desperdicio.id_desperdicio).label("cantidad"),
        ).filter(Desperdicio.fecha >= hace_30).group_by(Desperdicio.motivo).all()

        return [
            {"motivo": f.motivo, "costo": float(f.costo or 0), "cantidad": int(f.cantidad)}
            for f in filas
        ]
    finally:
        sesion.close()


@router.get("/top-platos")
def top_platos(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        hace_30 = date.today() - timedelta(days=30)
        filas = sesion.query(
            Plato.nombre,
            func.sum(DetalleVenta.cantidad).label("vendidos"),
            func.sum(DetalleVenta.subtotal).label("ingreso"),
        ).join(DetalleVenta, Plato.id_plato == DetalleVenta.id_plato)\
         .join(Venta, DetalleVenta.id_venta == Venta.id_venta)\
         .filter(Venta.fecha >= hace_30)\
         .group_by(Plato.nombre)\
         .order_by(func.sum(DetalleVenta.cantidad).desc())\
         .limit(10).all()

        return [
            {"plato": f.nombre, "vendidos": int(f.vendidos or 0), "ingreso": float(f.ingreso or 0)}
            for f in filas
        ]
    finally:
        sesion.close()


@router.get("/alertas")
def alertas(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        lista = []
        hoy = date.today()
        en_7_dias = hoy + timedelta(days=7)

        # Stock crítico
        criticos = sesion.query(Insumo).filter(
            Insumo.estado == True,
            Insumo.stock_disponible <= Insumo.stock_minimo,
        ).all()
        for i in criticos:
            lista.append({
                "tipo": "stock_bajo",
                "severidad": "advertencia",
                "titulo": f"Stock bajo: {i.nombre}",
                "mensaje": f"Stock actual: {float(i.stock_disponible or 0)} {i.unidad_medida}",
            })

        # Próximos a vencer
        por_vencer = sesion.query(Insumo).filter(
            Insumo.estado == True,
            Insumo.fecha_vencimiento != None,
            Insumo.fecha_vencimiento <= en_7_dias,
            Insumo.fecha_vencimiento >= hoy,
        ).all()
        for i in por_vencer:
            lista.append({
                "tipo": "vencimiento",
                "severidad": "critica",
                "titulo": f"Por vencer: {i.nombre}",
                "mensaje": f"Vence el {i.fecha_vencimiento}",
            })

        return lista
    finally:
        sesion.close()


@router.get("/eficiencia")
def indice_eficiencia(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        hoy     = date.today()
        hace_30 = hoy - timedelta(days=30)
        hace_60 = hoy - timedelta(days=60)

        # 1. Eficiencia de producción (40%) — menor sobrante = mejor
        prod = sesion.query(
            func.coalesce(func.sum(Produccion.cantidad_sobrante), 0).label("sobrante"),
            func.coalesce(func.sum(Produccion.cantidad_preparada), 0).label("preparado"),
        ).filter(Produccion.fecha >= hace_30).first()

        preparado = float(prod.preparado or 0)
        sobrante  = float(prod.sobrante  or 0)
        if preparado > 0:
            ratio = sobrante / preparado
            puntaje_prod = round(max(0.0, (1 - ratio * 2)) * 100, 1)
            detalle_prod = f"{ratio*100:.1f}% sobrante en producción"
        else:
            puntaje_prod = 50.0
            detalle_prod = "Sin datos de producción"

        # 2. Gestión de alertas (30%) — más resueltas/leídas = mejor
        total = int(sesion.query(func.count(AlertaInteligente.id_alerta)).scalar() or 0)
        gestionadas = int(
            sesion.query(func.count(AlertaInteligente.id_alerta))
            .filter(AlertaInteligente.estado.in_(["resuelta", "leida"]))
            .scalar() or 0
        )
        puntaje_alertas = round((gestionadas / total * 100) if total > 0 else 100.0, 1)
        detalle_alertas = f"{gestionadas}/{total} alertas gestionadas"

        # 3. Tendencia de desperdicio (30%) — reducir = mejor
        costo_act = float(
            sesion.query(func.coalesce(func.sum(Desperdicio.costo_estimado), 0))
            .filter(Desperdicio.fecha >= hace_30).scalar() or 0
        )
        costo_ant = float(
            sesion.query(func.coalesce(func.sum(Desperdicio.costo_estimado), 0))
            .filter(Desperdicio.fecha >= hace_60, Desperdicio.fecha < hace_30).scalar() or 0
        )
        if costo_ant > 0:
            cambio = (costo_act - costo_ant) / costo_ant  # negativo = mejora
            puntaje_desp = round(max(0.0, min(100.0, 70 - cambio * 100)), 1)
        else:
            puntaje_desp = 100.0 if costo_act == 0 else 50.0
        detalle_desp = f"S/ {costo_act:.0f} vs S/ {costo_ant:.0f} período anterior"

        indice = round(puntaje_prod * 0.4 + puntaje_alertas * 0.3 + puntaje_desp * 0.3, 1)
        color  = "verde" if indice >= 80 else ("amarillo" if indice >= 60 else "rojo")

        return {
            "indice": indice,
            "color":  color,
            "componentes": {
                "produccion":  {"puntaje": puntaje_prod,   "peso": 40, "detalle": detalle_prod},
                "alertas":     {"puntaje": puntaje_alertas,"peso": 30, "detalle": detalle_alertas},
                "desperdicio": {"puntaje": puntaje_desp,   "peso": 30, "detalle": detalle_desp},
            },
        }
    finally:
        sesion.close()


@router.get("/pedidos-sugeridos")
def pedidos_sugeridos(
    dias: int = 7,
    current_user: dict = Depends(obtener_usuario_actual),
):
    sesion = obtener_sesion()
    try:
        hoy     = date.today()
        hace_30 = hoy - timedelta(days=30)

        # Días reales con ventas en el período (divisor real, no siempre 30)
        dias_con_ventas = int(
            sesion.query(func.count(func.distinct(Venta.fecha)))
            .filter(Venta.fecha >= hace_30)
            .scalar() or 1
        )

        # Promedio diario de ventas por plato basado en días reales
        ventas_avg = {
            row.id_plato: float(row.total) / dias_con_ventas
            for row in sesion.query(
                DetalleVenta.id_plato,
                func.coalesce(func.sum(DetalleVenta.cantidad), 0).label("total"),
            ).join(Venta, DetalleVenta.id_venta == Venta.id_venta)
             .filter(Venta.fecha >= hace_30)
             .group_by(DetalleVenta.id_plato).all()
        }

        # Recetas agrupadas por plato
        recetas: dict[int, list] = {}
        for r in sesion.query(Receta).all():
            recetas.setdefault(r.id_plato, []).append((r.id_insumo, float(r.cantidad_usada)))

        # Necesidades proyectadas de insumos
        necesidades: dict[int, float] = {}
        for id_plato, avg in ventas_avg.items():
            for id_insumo, cant in recetas.get(id_plato, []):
                necesidades[id_insumo] = necesidades.get(id_insumo, 0) + avg * dias * cant

        # Generar lista de pedidos (solo los que faltan)
        pedidos = []
        for id_insumo, necesario in necesidades.items():
            ins = sesion.query(Insumo).filter(
                Insumo.id_insumo == id_insumo, Insumo.estado == True
            ).first()
            if not ins:
                continue
            stock    = float(ins.stock_disponible or 0)
            faltante = necesario - stock
            if faltante <= 0:
                continue
            pedidos.append({
                "id_insumo":       id_insumo,
                "insumo":          ins.nombre,
                "proveedor":       ins.proveedor or "Sin proveedor",
                "unidad":          ins.unidad_medida,
                "stock_actual":    round(stock,     3),
                "necesario":       round(necesario, 3),
                "cantidad_pedido": round(faltante,  3),
                "costo_estimado":  round(faltante * float(ins.costo_unitario or 0), 2),
            })

        pedidos.sort(key=lambda x: x["proveedor"])
        total_costo = round(sum(p["costo_estimado"] for p in pedidos), 2)
        return {
            "dias_proyeccion": dias,
            "dias_base_calculo": dias_con_ventas,
            "total_items": len(pedidos),
            "total_costo_estimado": total_costo,
            "pedidos": pedidos,
        }
    finally:
        sesion.close()
