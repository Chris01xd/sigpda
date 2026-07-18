"""
=================================================================
SIGPDA - Motor Interno de Alertas Inteligentes
=================================================================
Genera alertas preventivas y recomendaciones operativas
directamente desde el backend, sin depender de n8n ni de
servicios externos.  Cualquier PyME puede usar el sistema
de forma completamente autónoma.

Tipos de alerta generados automáticamente:
  RIESGO_SOBREPRODUCCION  — producción excede demanda histórica
  PRODUCTO_PROXIMO_VENCER — insumos con vencimiento <= 7 días
  STOCK_EXCESIVO          — stock muy por encima del mínimo
  BAJA_DEMANDA            — plato con caída de ventas > 20 %
  ALTO_DESPERDICIO        — costo de desperdicio elevado
  RECOMENDACION_MENU      — plato sin ventas en 30 días
  ALERTA_CRITICA          — múltiples factores de riesgo combinados

Niveles de riesgo: BAJO · MEDIO · ALTO · CRITICO
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.conexion import obtener_sesion
from database.modelos import (
    AlertaInteligente, Plato, Insumo, Produccion,
    Desperdicio, DetalleVenta, Venta,
)
from config.settings import UMBRAL_DESPERDICIO_PORCENTAJE

logger = logging.getLogger(__name__)

# ——— Constantes de tipos y niveles ———————————————————————

TIPO = {
    "SOBREPRODUCCION":    "RIESGO_SOBREPRODUCCION",
    "PROXIMO_VENCER":     "PRODUCTO_PROXIMO_VENCER",
    "STOCK_EXCESIVO":     "STOCK_EXCESIVO",
    "BAJA_DEMANDA":       "BAJA_DEMANDA",
    "ALTO_DESPERDICIO":   "ALTO_DESPERDICIO",
    "RECOMENDACION_MENU": "RECOMENDACION_MENU",
    "CRITICA":            "ALERTA_CRITICA",
}

NIVEL = {"BAJO": "BAJO", "MEDIO": "MEDIO", "ALTO": "ALTO", "CRITICO": "CRITICO"}

ESTADO = {"PENDIENTE": "pendiente", "LEIDA": "leida", "RESUELTA": "resuelta"}

# Etiquetas de clima y evento para mensajes
_CLIMA_LABEL  = {1: "soleado", 2: "nublado", 3: "lluvioso"}
_EVENTO_LABEL = {0: "sin evento especial", 1: "evento local", 2: "feriado nacional"}


# ================================================================
# HELPERS INTERNOS
# ================================================================

def _nivel_por_porcentaje(pct: float, umbrales: tuple[float, float, float]) -> str:
    """Determina el nivel de riesgo según el porcentaje y los umbrales dados."""
    b, m, a = umbrales
    if pct < b:   return NIVEL["BAJO"]
    if pct < m:   return NIVEL["MEDIO"]
    if pct < a:   return NIVEL["ALTO"]
    return NIVEL["CRITICO"]


def _existe_alerta_pendiente(
    sesion: Session,
    tipo: str,
    id_plato: int | None = None,
    id_insumo: int | None = None,
) -> bool:
    """Evita duplicar alertas pendientes del mismo tipo para el mismo recurso."""
    ayer = datetime.utcnow() - timedelta(hours=24)
    q = sesion.query(AlertaInteligente).filter(
        AlertaInteligente.tipo_alerta == tipo,
        AlertaInteligente.estado == ESTADO["PENDIENTE"],
        AlertaInteligente.fecha_generacion >= ayer,
    )
    if id_plato  is not None: q = q.filter(AlertaInteligente.id_plato  == id_plato)
    if id_insumo is not None: q = q.filter(AlertaInteligente.id_insumo == id_insumo)
    return q.first() is not None


def _guardar(sesion: Session, alerta: AlertaInteligente) -> None:
    sesion.add(alerta)


# ================================================================
# GENERADOR DE RECOMENDACIONES OPERATIVAS
# ================================================================

def generar_recomendacion_operativa(
    tipo: str,
    nombre: str,
    nivel: str,
    datos: dict,
    clima: int = 2,
    evento: int = 0,
) -> str:
    """
    Genera un texto de recomendación práctica según el tipo de alerta,
    el nivel de riesgo y el contexto ambiental (clima y evento).

    Las recomendaciones están escritas en lenguaje sencillo para
    que el personal de la PyME pueda actuar inmediatamente.
    """
    ctx = ""
    if clima == 3 or evento >= 1:
        ctx = (
            f" Considerar que el clima es {_CLIMA_LABEL.get(clima, '')} "
            f"y hay {_EVENTO_LABEL.get(evento, '')} hoy, lo que puede "
            f"{'aumentar' if evento >= 1 else 'reducir'} la demanda."
        )

    if tipo == TIPO["SOBREPRODUCCION"]:
        pct = datos.get("porcentaje", 0)
        ajuste = min(int(pct * 0.8), 40)
        return (
            f"Reducir la producción diaria de '{nombre}' en aproximadamente {ajuste} %. "
            f"Actualmente se desperdicia el {pct:.1f} % de lo preparado. "
            f"Usar el historial de ventas de los últimos 7 días como referencia.{ctx}"
        )

    if tipo == TIPO["PROXIMO_VENCER"]:
        dias = datos.get("dias", 0)
        stock = datos.get("stock", 0)
        return (
            f"Dar uso prioritario a '{nombre}' antes de {dias} día(s). "
            f"Stock disponible: {stock:.2f} unidades. "
            f"Incorporar como ingrediente especial del día o aplicar descuento en el menú.{ctx}"
        )

    if tipo == TIPO["STOCK_EXCESIVO"]:
        ratio = datos.get("ratio", 0)
        return (
            f"El stock de '{nombre}' es {ratio:.1f}x el mínimo recomendado. "
            f"Pausar pedidos al proveedor y priorizar el consumo. "
            f"Revisar si hay platos que pueden incorporar este insumo en mayor cantidad.{ctx}"
        )

    if tipo == TIPO["BAJA_DEMANDA"]:
        caida = datos.get("caida_pct", 0)
        return (
            f"Las ventas de '{nombre}' cayeron {caida:.1f} % respecto al mes anterior. "
            f"Evaluar una promoción, reducir precio temporalmente o mejorar presentación. "
            f"Considerar reducir producción mientras se implementa la mejora.{ctx}"
        )

    if tipo == TIPO["ALTO_DESPERDICIO"]:
        costo = datos.get("costo", 0)
        return (
            f"El costo de desperdicio de '{nombre}' fue S/ {costo:.2f} en los últimos 30 días. "
            f"Revisar porciones servidas, ajustar receta y capacitar al personal. "
            f"Registrar el motivo de cada desperdicio para identificar la causa raíz.{ctx}"
        )

    if tipo == TIPO["RECOMENDACION_MENU"]:
        return (
            f"'{nombre}' no registra ventas en los últimos 30 días. "
            f"Considerar retirarlo del menú, actualizar su presentación o incluirlo en "
            f"un combo con mayor rotación para estimular su consumo.{ctx}"
        )

    if tipo == TIPO["CRITICA"]:
        return (
            f"'{nombre}' presenta múltiples factores de riesgo simultáneos: "
            f"baja demanda y alto desperdicio. Acción inmediata recomendada: "
            f"suspender temporalmente la producción, revisar la receta y consultar "
            f"con el equipo si debe mantenerse en el menú.{ctx}"
        )

    return f"Revisar el estado de '{nombre}' y tomar las acciones correctivas necesarias.{ctx}"


# ================================================================
# CÁLCULO DE RIESGO DE DESPERDICIO POR PLATO
# ================================================================

def calcular_riesgo_desperdicio(id_plato: int, sesion: Session) -> dict:
    """
    Calcula el porcentaje de riesgo de desperdicio para un plato
    combinando: sobrante de producción, costo de desperdicios y
    tendencia de ventas de los últimos 30 días.

    Retorna:
        porcentaje: float  (0–100, mayor = más riesgo)
        nivel:      str    BAJO / MEDIO / ALTO / CRITICO
    """
    hoy = date.today()
    hace_30 = hoy - timedelta(days=30)

    # Sobrante de producción
    prod = sesion.query(
        func.coalesce(func.sum(Produccion.cantidad_sobrante), 0).label("sobrante"),
        func.coalesce(func.sum(Produccion.cantidad_preparada), 0).label("preparado"),
    ).filter(
        Produccion.id_plato == id_plato,
        Produccion.fecha >= hace_30,
    ).first()

    pct_sobrante = 0.0
    if prod and float(prod.preparado or 0) > 0:
        pct_sobrante = (float(prod.sobrante) / float(prod.preparado)) * 100

    # Costo de desperdicios
    costo = sesion.query(
        func.coalesce(func.sum(Desperdicio.costo_estimado), 0)
    ).filter(
        Desperdicio.id_plato == id_plato,
        Desperdicio.fecha >= hace_30,
    ).scalar() or 0.0

    pct_costo = min(float(costo) / 10, 50)  # normalizar: 500 soles = 50 pts

    porcentaje = min((pct_sobrante * 0.6 + pct_costo * 0.4), 100)
    nivel = _nivel_por_porcentaje(porcentaje, (15.0, 35.0, 60.0))

    return {"porcentaje": round(porcentaje, 2), "nivel": nivel}


# ================================================================
# FUNCIÓN PRINCIPAL — GENERADOR DE ALERTAS INTELIGENTES
# ================================================================

def generar_alertas_inteligentes(clima: int = 2, evento: int = 0) -> dict:
    """
    Motor principal del sistema de alertas.  Revisa el estado actual
    de la PyME y genera alertas automáticas persistidas en la BD.

    No requiere n8n ni ningún servicio externo.
    Puede ejecutarse en cualquier momento desde el backend.

    Parámetros:
        clima  : contexto climático (1=soleado, 2=nublado, 3=lluvia)
        evento : tipo de evento    (0=normal, 1=local, 2=feriado)

    Retorna:
        Resumen con total de alertas creadas, desglose por tipo y nivel.
    """
    sesion = obtener_sesion()
    creadas: list[dict] = []
    hoy = date.today()
    hace_30  = hoy - timedelta(days=30)
    hace_60  = hoy - timedelta(days=60)
    en_7dias = hoy + timedelta(days=7)

    try:
        # ——— 1. RIESGO DE SOBREPRODUCCIÓN ———————————————————————
        sobrantes = sesion.query(
            Plato.id_plato,
            Plato.nombre,
            func.coalesce(func.sum(Produccion.cantidad_sobrante), 0).label("sobrante"),
            func.coalesce(func.sum(Produccion.cantidad_preparada), 0).label("preparado"),
        ).join(Produccion, Plato.id_plato == Produccion.id_plato)\
         .filter(Produccion.fecha >= hace_30)\
         .group_by(Plato.id_plato, Plato.nombre).all()

        for s in sobrantes:
            preparado = float(s.preparado or 0)
            if preparado <= 0:
                continue
            pct = (float(s.sobrante) / preparado) * 100
            if pct < 10.0:
                continue
            if _existe_alerta_pendiente(sesion, TIPO["SOBREPRODUCCION"], id_plato=s.id_plato):
                continue
            nivel = _nivel_por_porcentaje(pct, (10.0, 25.0, 45.0))
            rec   = generar_recomendacion_operativa(
                TIPO["SOBREPRODUCCION"], s.nombre, nivel,
                {"porcentaje": pct}, clima, evento,
            )
            alerta = AlertaInteligente(
                tipo_alerta      = TIPO["SOBREPRODUCCION"],
                nivel_riesgo     = nivel,
                titulo           = f"Riesgo sobreproducción: {s.nombre}",
                descripcion      = (
                    f"El {pct:.1f} % de la producción de '{s.nombre}' "
                    f"fue sobrante en los últimos 30 días "
                    f"({int(s.sobrante)} de {int(preparado)} unidades)."
                ),
                recomendacion    = rec,
                id_plato         = s.id_plato,
                valor_predicho   = round(preparado - float(s.sobrante), 2),
                valor_actual     = float(s.sobrante),
                porcentaje_riesgo = round(pct, 2),
            )
            _guardar(sesion, alerta)
            creadas.append({"tipo": TIPO["SOBREPRODUCCION"], "nivel": nivel})

        # ——— 2. PRODUCTO PRÓXIMO A VENCER ————————————————————————
        por_vencer = sesion.query(Insumo).filter(
            Insumo.estado == True,
            Insumo.fecha_vencimiento.isnot(None),
            Insumo.fecha_vencimiento >= hoy,
            Insumo.fecha_vencimiento <= en_7dias,
        ).all()

        for insumo in por_vencer:
            dias = (insumo.fecha_vencimiento - hoy).days
            if _existe_alerta_pendiente(sesion, TIPO["PROXIMO_VENCER"], id_insumo=insumo.id_insumo):
                continue
            if   dias <= 1: nivel = NIVEL["CRITICO"]
            elif dias <= 2: nivel = NIVEL["ALTO"]
            elif dias <= 4: nivel = NIVEL["MEDIO"]
            else:           nivel = NIVEL["BAJO"]
            stock = float(insumo.stock_disponible or 0)
            rec   = generar_recomendacion_operativa(
                TIPO["PROXIMO_VENCER"], insumo.nombre, nivel,
                {"dias": dias, "stock": stock}, clima, evento,
            )
            alerta = AlertaInteligente(
                tipo_alerta      = TIPO["PROXIMO_VENCER"],
                nivel_riesgo     = nivel,
                titulo           = f"Vence en {dias} día(s): {insumo.nombre}",
                descripcion      = (
                    f"'{insumo.nombre}' vence el {insumo.fecha_vencimiento}. "
                    f"Stock disponible: {stock:.2f} {insumo.unidad_medida}."
                ),
                recomendacion    = rec,
                id_insumo        = insumo.id_insumo,
                valor_actual     = float(dias),
                valor_predicho   = stock,
                porcentaje_riesgo = max(0.0, round((7 - dias) / 7 * 100, 2)),
            )
            _guardar(sesion, alerta)
            creadas.append({"tipo": TIPO["PROXIMO_VENCER"], "nivel": nivel})

        # ——— 3. STOCK EXCESIVO ————————————————————————————————————
        excesivos = sesion.query(Insumo).filter(
            Insumo.estado == True,
            Insumo.stock_minimo > 0,
            Insumo.stock_disponible > Insumo.stock_minimo * 3,
        ).all()

        for insumo in excesivos:
            ratio = float(insumo.stock_disponible) / float(insumo.stock_minimo)
            if _existe_alerta_pendiente(sesion, TIPO["STOCK_EXCESIVO"], id_insumo=insumo.id_insumo):
                continue
            nivel = _nivel_por_porcentaje(ratio, (4.0, 6.0, 10.0))
            rec   = generar_recomendacion_operativa(
                TIPO["STOCK_EXCESIVO"], insumo.nombre, nivel,
                {"ratio": ratio}, clima, evento,
            )
            alerta = AlertaInteligente(
                tipo_alerta       = TIPO["STOCK_EXCESIVO"],
                nivel_riesgo      = nivel,
                titulo            = f"Stock excesivo: {insumo.nombre}",
                descripcion       = (
                    f"Stock de '{insumo.nombre}': {float(insumo.stock_disponible):.2f} "
                    f"{insumo.unidad_medida} ({ratio:.1f}x el mínimo recomendado)."
                ),
                recomendacion     = rec,
                id_insumo         = insumo.id_insumo,
                valor_actual      = float(insumo.stock_disponible),
                valor_predicho    = float(insumo.stock_minimo),
                porcentaje_riesgo = round(min(ratio * 10, 100), 2),
            )
            _guardar(sesion, alerta)
            creadas.append({"tipo": TIPO["STOCK_EXCESIVO"], "nivel": nivel})

        # ——— 4. BAJA DEMANDA ——————————————————————————————————————
        # Ventas últimos 30 días vs 30 días anteriores por plato
        ventas_recientes = {
            row.id_plato: int(row.vendidos)
            for row in sesion.query(
                DetalleVenta.id_plato,
                func.coalesce(func.sum(DetalleVenta.cantidad), 0).label("vendidos"),
            ).join(Venta, DetalleVenta.id_venta == Venta.id_venta)
             .filter(Venta.fecha >= hace_30)
             .group_by(DetalleVenta.id_plato).all()
        }
        ventas_anteriores = {
            row.id_plato: int(row.vendidos)
            for row in sesion.query(
                DetalleVenta.id_plato,
                func.coalesce(func.sum(DetalleVenta.cantidad), 0).label("vendidos"),
            ).join(Venta, DetalleVenta.id_venta == Venta.id_venta)
             .filter(Venta.fecha >= hace_60, Venta.fecha < hace_30)
             .group_by(DetalleVenta.id_plato).all()
        }

        platos_activos = sesion.query(Plato).filter(Plato.estado == True).all()

        for plato in platos_activos:
            previo  = ventas_anteriores.get(plato.id_plato, 0)
            reciente = ventas_recientes.get(plato.id_plato, 0)
            if previo <= 0:
                continue
            caida = (previo - reciente) / previo * 100
            if caida < 20.0:
                continue
            if _existe_alerta_pendiente(sesion, TIPO["BAJA_DEMANDA"], id_plato=plato.id_plato):
                continue
            nivel = _nivel_por_porcentaje(caida, (20.0, 40.0, 65.0))
            rec   = generar_recomendacion_operativa(
                TIPO["BAJA_DEMANDA"], plato.nombre, nivel,
                {"caida_pct": caida}, clima, evento,
            )
            alerta = AlertaInteligente(
                tipo_alerta       = TIPO["BAJA_DEMANDA"],
                nivel_riesgo      = nivel,
                titulo            = f"Baja demanda: {plato.nombre}",
                descripcion       = (
                    f"Las ventas de '{plato.nombre}' cayeron {caida:.1f} % "
                    f"(de {previo} a {reciente} unidades en los últimos 30 días)."
                ),
                recomendacion     = rec,
                id_plato          = plato.id_plato,
                valor_predicho    = float(previo),
                valor_actual      = float(reciente),
                porcentaje_riesgo = round(caida, 2),
            )
            _guardar(sesion, alerta)
            creadas.append({"tipo": TIPO["BAJA_DEMANDA"], "nivel": nivel})

        # ——— 5. ALTO DESPERDICIO ——————————————————————————————————
        desperdicios = sesion.query(
            Plato.id_plato,
            Plato.nombre,
            func.coalesce(func.sum(Desperdicio.costo_estimado), 0).label("costo"),
            func.coalesce(func.sum(Desperdicio.cantidad), 0).label("cantidad"),
        ).join(Desperdicio, Plato.id_plato == Desperdicio.id_plato)\
         .filter(Desperdicio.fecha >= hace_30)\
         .group_by(Plato.id_plato, Plato.nombre).all()

        platos_con_desperdicio_alto: set[int] = set()

        for d in desperdicios:
            costo = float(d.costo or 0)
            if costo < 20.0:
                continue
            if _existe_alerta_pendiente(sesion, TIPO["ALTO_DESPERDICIO"], id_plato=d.id_plato):
                continue
            nivel = _nivel_por_porcentaje(costo, (20.0, 60.0, 120.0))
            if nivel in (NIVEL["ALTO"], NIVEL["CRITICO"]):
                platos_con_desperdicio_alto.add(d.id_plato)
            rec = generar_recomendacion_operativa(
                TIPO["ALTO_DESPERDICIO"], d.nombre, nivel,
                {"costo": costo}, clima, evento,
            )
            alerta = AlertaInteligente(
                tipo_alerta       = TIPO["ALTO_DESPERDICIO"],
                nivel_riesgo      = nivel,
                titulo            = f"Alto desperdicio: {d.nombre}",
                descripcion       = (
                    f"Costo de desperdicio de '{d.nombre}': S/ {costo:.2f} "
                    f"en los últimos 30 días ({float(d.cantidad):.2f} unidades desperdiciadas)."
                ),
                recomendacion     = rec,
                id_plato          = d.id_plato,
                valor_actual      = costo,
                valor_predicho    = 0.0,
                porcentaje_riesgo = round(min(costo / 2, 100), 2),
            )
            _guardar(sesion, alerta)
            creadas.append({"tipo": TIPO["ALTO_DESPERDICIO"], "nivel": nivel})

        # ——— 6. RECOMENDACIÓN DE MENÚ — PLATOS SIN VENTAS ————————
        ids_con_ventas = set(ventas_recientes.keys())
        for plato in platos_activos:
            if plato.id_plato in ids_con_ventas:
                continue
            if _existe_alerta_pendiente(sesion, TIPO["RECOMENDACION_MENU"], id_plato=plato.id_plato):
                continue
            rec = generar_recomendacion_operativa(
                TIPO["RECOMENDACION_MENU"], plato.nombre, NIVEL["BAJO"], {}, clima, evento,
            )
            alerta = AlertaInteligente(
                tipo_alerta       = TIPO["RECOMENDACION_MENU"],
                nivel_riesgo      = NIVEL["BAJO"],
                titulo            = f"Sin ventas en 30 días: {plato.nombre}",
                descripcion       = (
                    f"'{plato.nombre}' no registra ventas en los últimos 30 días. "
                    f"Evaluar si debe permanecer en el menú."
                ),
                recomendacion     = rec,
                id_plato          = plato.id_plato,
                valor_actual      = 0.0,
                porcentaje_riesgo = 0.0,
            )
            _guardar(sesion, alerta)
            creadas.append({"tipo": TIPO["RECOMENDACION_MENU"], "nivel": NIVEL["BAJO"]})

        # ——— 7. ALERTA CRÍTICA — FACTORES COMBINADOS ————————————
        # Platos con baja demanda Y alto desperdicio simultáneamente
        platos_baja_demanda = {
            a["tipo"]: True
            for a in creadas
            if a["tipo"] == TIPO["BAJA_DEMANDA"]
        }
        ids_baja_demanda = {
            row.id_plato
            for row in sesion.query(AlertaInteligente.id_plato).filter(
                AlertaInteligente.tipo_alerta == TIPO["BAJA_DEMANDA"],
                AlertaInteligente.estado == ESTADO["PENDIENTE"],
                AlertaInteligente.id_plato.isnot(None),
            ).all()
        }
        ids_criticos = ids_baja_demanda & platos_con_desperdicio_alto

        for id_plato in ids_criticos:
            if _existe_alerta_pendiente(sesion, TIPO["CRITICA"], id_plato=id_plato):
                continue
            plato = sesion.query(Plato).filter(Plato.id_plato == id_plato).first()
            if not plato:
                continue
            rec = generar_recomendacion_operativa(
                TIPO["CRITICA"], plato.nombre, NIVEL["CRITICO"], {}, clima, evento,
            )
            alerta = AlertaInteligente(
                tipo_alerta       = TIPO["CRITICA"],
                nivel_riesgo      = NIVEL["CRITICO"],
                titulo            = f"Alerta crítica: {plato.nombre}",
                descripcion       = (
                    f"'{plato.nombre}' presenta baja demanda y alto costo de "
                    f"desperdicio simultáneamente. Requiere atención inmediata."
                ),
                recomendacion     = rec,
                id_plato          = id_plato,
                porcentaje_riesgo = 100.0,
            )
            _guardar(sesion, alerta)
            creadas.append({"tipo": TIPO["CRITICA"], "nivel": NIVEL["CRITICO"]})

        sesion.commit()
        logger.info(f"Alertas inteligentes generadas: {len(creadas)}")

    except Exception as exc:
        sesion.rollback()
        logger.error(f"Error generando alertas: {exc}")
        raise
    finally:
        sesion.close()

    # Resumen por tipo y nivel
    por_tipo  = {}
    por_nivel = {}
    for a in creadas:
        por_tipo[a["tipo"]]   = por_tipo.get(a["tipo"], 0) + 1
        por_nivel[a["nivel"]] = por_nivel.get(a["nivel"], 0) + 1

    return {
        "total_generadas": len(creadas),
        "por_tipo":        por_tipo,
        "por_nivel":       por_nivel,
        "fecha":           datetime.utcnow().isoformat(),
        "alertas":         creadas,
    }


# ================================================================
# CONSULTA DE ALERTAS ACTIVAS
# ================================================================

def obtener_alertas_activas(
    limit: int = 50,
    tipo: str | None = None,
    nivel: str | None = None,
    estado: str = "pendiente",
) -> list[dict]:
    """
    Retorna alertas filtradas por tipo, nivel y estado.
    Por defecto devuelve las alertas pendientes, ordenadas por
    nivel de riesgo descendente (CRITICO primero).
    """
    sesion = obtener_sesion()
    try:
        ORDEN_NIVEL = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "BAJO": 3}

        q = sesion.query(AlertaInteligente)
        if estado:
            q = q.filter(AlertaInteligente.estado == estado)
        if tipo:
            q = q.filter(AlertaInteligente.tipo_alerta == tipo)
        if nivel:
            q = q.filter(AlertaInteligente.nivel_riesgo == nivel)

        alertas = q.order_by(
            AlertaInteligente.fecha_generacion.desc()
        ).limit(limit).all()

        resultado = []
        for a in alertas:
            resultado.append({
                "id_alerta":        a.id_alerta,
                "tipo_alerta":      a.tipo_alerta,
                "nivel_riesgo":     a.nivel_riesgo,
                "titulo":           a.titulo,
                "descripcion":      a.descripcion,
                "recomendacion":    a.recomendacion,
                "fecha_generacion": a.fecha_generacion.isoformat() if a.fecha_generacion else None,
                "estado":           a.estado,
                "id_plato":         a.id_plato,
                "id_insumo":        a.id_insumo,
                "plato":            a.plato.nombre if a.plato else None,
                "insumo":           a.insumo.nombre if a.insumo else None,
                "valor_predicho":   a.valor_predicho,
                "valor_actual":     a.valor_actual,
                "porcentaje_riesgo": a.porcentaje_riesgo,
            })

        # Ordenar por prioridad de nivel
        resultado.sort(key=lambda x: ORDEN_NIVEL.get(x["nivel_riesgo"], 9))
        return resultado
    finally:
        sesion.close()
