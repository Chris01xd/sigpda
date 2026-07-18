"""
=================================================================
SIGPDA - Generador de Reportes PDF
=================================================================
Construye reportes operativos / gerenciales / de auditoría usando
ReportLab. Cada reporte incluye encabezado, fecha, usuario que lo
generó, tablas, resumen ejecutivo y opcionalmente gráficos.
"""

from datetime import date, datetime, timedelta
from io import BytesIO

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

from config import settings
from database import obtener_sesion
from database.modelos import (
    Plato, Insumo, Restaurante, Venta, DetalleVenta,
    Desperdicio, Bitacora, Prediccion, Usuario
)
from utils.helpers import formato_moneda


# ----------------------------------------------------------------
# UTILIDADES INTERNAS
# ----------------------------------------------------------------

def _estilos():
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle(
        name="TituloSIGPDA",
        parent=estilos["Heading1"],
        fontSize=18, alignment=1, textColor=colors.HexColor("#2c3e50"),
        spaceAfter=14,
    ))
    estilos.add(ParagraphStyle(
        name="SubSIGPDA",
        parent=estilos["Heading2"],
        fontSize=12, textColor=colors.HexColor("#16a085"),
        spaceAfter=6,
    ))
    estilos.add(ParagraphStyle(
        name="MetaSIGPDA",
        parent=estilos["Normal"],
        fontSize=9, textColor=colors.gray,
    ))
    return estilos


def _encabezado(titulo: str, usuario: str) -> list:
    estilos = _estilos()
    elementos = []
    elementos.append(Paragraph(f"<b>{settings.NOMBRE_SISTEMA}</b>", estilos["MetaSIGPDA"]))
    elementos.append(Paragraph(titulo, estilos["TituloSIGPDA"]))
    elementos.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} · "
        f"Usuario: {usuario}",
        estilos["MetaSIGPDA"],
    ))
    elementos.append(Spacer(1, 0.5 * cm))
    return elementos


def _tabla(df: pd.DataFrame, max_filas: int = 50) -> Table:
    """Convierte un DataFrame en un Table de ReportLab con estilo."""
    if df is None or df.empty:
        return Paragraph("<i>Sin datos</i>", _estilos()["Normal"])

    df = df.head(max_filas).copy()
    # Convertir todo a string para evitar problemas
    df = df.astype(str)
    datos = [list(df.columns)] + df.values.tolist()
    tabla = Table(datos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#ecf0f1"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.gray),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabla


def _resumen(texto: str) -> list:
    estilos = _estilos()
    return [
        Paragraph("Resumen ejecutivo", estilos["SubSIGPDA"]),
        Paragraph(texto, estilos["Normal"]),
        Spacer(1, 0.5 * cm),
    ]


def _construir_pdf(elementos: list) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    doc.build(elementos)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def _usuario_actual(usuario: str = "Sistema") -> str:
    return usuario


# ----------------------------------------------------------------
# REPORTES ESPECÍFICOS
# ----------------------------------------------------------------

def reporte_operacional_diario(fecha_obj: date | None = None) -> bytes:
    fecha_obj = fecha_obj or date.today()
    sesion = obtener_sesion()
    elementos = _encabezado(f"Reporte Operacional Diario - {fecha_obj}", _usuario_actual())

    # Ventas
    ventas = sesion.query(Venta).filter(Venta.fecha == fecha_obj).all()
    total_v = sum(float(v.total or 0) for v in ventas)
    desp = sesion.query(Desperdicio).filter(Desperdicio.fecha == fecha_obj).all()
    total_d_costo = sum(float(d.costo_estimado or 0) for d in desp)
    pct = (total_d_costo / total_v * 100) if total_v > 0 else 0

    elementos += _resumen(
        f"Total ventas: <b>{formato_moneda(total_v)}</b> · "
        f"Tickets: <b>{len(ventas)}</b> · "
        f"Costo desperdicio: <b>{formato_moneda(total_d_costo)}</b> · "
        f"% Desperdicio: <b>{pct:.2f}%</b>"
    )

    # Tabla de ventas
    df_v = pd.DataFrame([{
        "ID": v.id_venta, "Hora": v.hora,
        "Total": formato_moneda(float(v.total or 0)),
        "Pago": v.metodo_pago,
    } for v in ventas])
    elementos.append(Paragraph("Ventas del día", _estilos()["SubSIGPDA"]))
    elementos.append(_tabla(df_v))
    elementos.append(Spacer(1, 0.5 * cm))

    # Tabla de desperdicios
    df_d = pd.DataFrame([{
        "ID": d.id_desperdicio, "Tipo": d.tipo,
        "Cantidad": float(d.cantidad or 0),
        "Motivo": d.motivo,
        "Costo": formato_moneda(float(d.costo_estimado or 0)),
    } for d in desp])
    elementos.append(Paragraph("Desperdicios del día", _estilos()["SubSIGPDA"]))
    elementos.append(_tabla(df_d))

    sesion.close()
    return _construir_pdf(elementos)


def reporte_semanal_ventas(fecha_fin: date | None = None) -> bytes:
    fecha_fin = fecha_fin or date.today()
    fecha_ini = fecha_fin - timedelta(days=6)
    sesion = obtener_sesion()
    elementos = _encabezado(
        f"Reporte Semanal de Ventas ({fecha_ini} - {fecha_fin})",
        _usuario_actual()
    )

    ventas = sesion.query(Venta).filter(
        Venta.fecha >= fecha_ini, Venta.fecha <= fecha_fin
    ).all()
    total = sum(float(v.total or 0) for v in ventas)
    promedio_diario = total / 7

    elementos += _resumen(
        f"Total semana: <b>{formato_moneda(total)}</b> · "
        f"Tickets: <b>{len(ventas)}</b> · "
        f"Promedio diario: <b>{formato_moneda(promedio_diario)}</b>"
    )

    # Top platos
    detalles = sesion.query(DetalleVenta).join(Venta).filter(
        Venta.fecha >= fecha_ini, Venta.fecha <= fecha_fin
    ).all()
    top = {}
    for d in detalles:
        pl = sesion.query(Plato).filter(Plato.id_plato == d.id_plato).first()
        if pl:
            top[pl.nombre] = top.get(pl.nombre, 0) + d.cantidad
    df_top = pd.DataFrame([{"Plato": k, "Cantidad": v}
                            for k, v in top.items()])\
        .sort_values("Cantidad", ascending=False).head(10)
    elementos.append(Paragraph("Top 10 platos vendidos", _estilos()["SubSIGPDA"]))
    elementos.append(_tabla(df_top))
    elementos.append(Spacer(1, 0.5 * cm))

    # Ventas diarias
    df_v_dia = pd.DataFrame([{
        "Fecha": v.fecha, "Hora": v.hora,
        "Total": float(v.total or 0)
    } for v in ventas])
    if not df_v_dia.empty:
        df_dia = df_v_dia.groupby("Fecha")["Total"].agg(["sum", "count"]).reset_index()
        df_dia.columns = ["Fecha", "Total", "Tickets"]
        df_dia["Total"] = df_dia["Total"].apply(formato_moneda)
        elementos.append(Paragraph("Resumen diario", _estilos()["SubSIGPDA"]))
        elementos.append(_tabla(df_dia))

    sesion.close()
    return _construir_pdf(elementos)


def reporte_mensual_desperdicio(fecha_ref: date | None = None) -> bytes:
    fecha_ref = fecha_ref or date.today()
    fecha_ini = fecha_ref.replace(day=1)
    sesion = obtener_sesion()
    elementos = _encabezado(
        f"Reporte Mensual de Desperdicio ({fecha_ini.strftime('%B %Y')})",
        _usuario_actual()
    )

    desp = sesion.query(Desperdicio).filter(
        Desperdicio.fecha >= fecha_ini, Desperdicio.fecha <= fecha_ref
    ).all()
    total_costo = sum(float(d.costo_estimado or 0) for d in desp)
    total_cant = sum(float(d.cantidad or 0) for d in desp)

    ventas = sesion.query(Venta).filter(
        Venta.fecha >= fecha_ini, Venta.fecha <= fecha_ref
    ).all()
    total_ventas = sum(float(v.total or 0) for v in ventas)
    pct = (total_costo / total_ventas * 100) if total_ventas > 0 else 0

    elementos += _resumen(
        f"Costo total desperdicio: <b>{formato_moneda(total_costo)}</b> · "
        f"Cantidad: <b>{total_cant:.2f}</b> · "
        f"% sobre ventas: <b>{pct:.2f}%</b> "
        f"(umbral {settings.UMBRAL_DESPERDICIO_PORCENTAJE}%)"
    )

    df = pd.DataFrame([{
        "Fecha": d.fecha, "Tipo": d.tipo,
        "Motivo": d.motivo,
        "Cantidad": float(d.cantidad or 0),
        "Costo": formato_moneda(float(d.costo_estimado or 0)),
    } for d in desp])
    elementos.append(Paragraph("Detalle de desperdicios", _estilos()["SubSIGPDA"]))
    elementos.append(_tabla(df, max_filas=80))

    # Por motivo
    if not df.empty:
        elementos.append(Spacer(1, 0.5 * cm))
        df_mot = df.groupby("Motivo").size().reset_index(name="Casos")
        elementos.append(Paragraph("Desperdicios por motivo", _estilos()["SubSIGPDA"]))
        elementos.append(_tabla(df_mot))

    sesion.close()
    return _construir_pdf(elementos)


def reporte_prediccion_demanda() -> bytes:
    sesion = obtener_sesion()
    elementos = _encabezado("Reporte de Predicción de Demanda", _usuario_actual())

    preds = sesion.query(Prediccion).order_by(
        Prediccion.fecha_generacion.desc()
    ).limit(100).all()

    if not preds:
        elementos.append(Paragraph(
            "<i>Aún no se han generado predicciones.</i>", _estilos()["Normal"]
        ))
    else:
        elementos += _resumen(
            f"Total de predicciones registradas (últimas 100): <b>{len(preds)}</b>. "
            "Se incluyen demanda estimada, recomendación de producción, "
            "modelo utilizado, error y nivel de confianza."
        )
        df = pd.DataFrame([{
            "Generada": p.fecha_generacion.strftime("%d/%m %H:%M") if p.fecha_generacion else "",
            "Plato": (sesion.query(Plato).filter(Plato.id_plato == p.id_plato).first().nombre
                      if p.id_plato else ""),
            "Fecha objetivo": p.fecha_objetivo,
            "Demanda": round(p.demanda_estimada, 2),
            "Producción rec.": p.recomendacion_produccion,
            "Riesgo": p.riesgo_desperdicio,
            "Modelo": p.modelo_usado,
            "MAE": round(p.mae or 0, 2),
            "R²": round(p.r2 or 0, 3),
            "Confianza": f"{round((p.confianza or 0)*100, 1)}%",
        } for p in preds])
        elementos.append(_tabla(df, max_filas=100))

    sesion.close()
    return _construir_pdf(elementos)


def reporte_insumos_por_vencer() -> bytes:
    sesion = obtener_sesion()
    elementos = _encabezado("Reporte de Insumos por Vencer", _usuario_actual())

    hoy = date.today()
    insumos = sesion.query(Insumo).filter(Insumo.estado.is_(True)).all()
    lista = []
    for ins in insumos:
        if ins.fecha_vencimiento:
            dias = (ins.fecha_vencimiento - hoy).days
            estado = "VENCIDO" if dias < 0 else (
                "Por vencer" if dias <= 7 else "OK"
            )
            if estado != "OK":
                lista.append({
                    "Insumo": ins.nombre,
                    "Stock": float(ins.stock_disponible or 0),
                    "Unidad": ins.unidad_medida,
                    "Vencimiento": ins.fecha_vencimiento,
                    "Días": dias,
                    "Estado": estado,
                })
    df = pd.DataFrame(lista).sort_values("Días") if lista else pd.DataFrame()

    elementos += _resumen(
        f"Insumos vencidos o próximos a vencer (≤ 7 días): <b>{len(lista)}</b>"
    )
    elementos.append(_tabla(df, max_filas=100))

    sesion.close()
    return _construir_pdf(elementos)


def reporte_gestion_administrador() -> bytes:
    """Reporte ejecutivo consolidado para administrador."""
    sesion = obtener_sesion()
    elementos = _encabezado("Reporte de Gestión Ejecutiva", _usuario_actual())

    hoy = date.today()
    hace_30 = hoy - timedelta(days=30)

    ventas = sesion.query(Venta).filter(
        Venta.fecha >= hace_30, Venta.fecha <= hoy
    ).all()
    desp = sesion.query(Desperdicio).filter(
        Desperdicio.fecha >= hace_30, Desperdicio.fecha <= hoy
    ).all()
    total_v = sum(float(v.total or 0) for v in ventas)
    total_d = sum(float(d.costo_estimado or 0) for d in desp)
    pct = (total_d / total_v * 100) if total_v > 0 else 0

    elementos += _resumen(
        f"Periodo: últimos 30 días ({hace_30} a {hoy}).<br/>"
        f"Ventas: <b>{formato_moneda(total_v)}</b><br/>"
        f"Costo desperdicio: <b>{formato_moneda(total_d)}</b><br/>"
        f"% desperdicio: <b>{pct:.2f}%</b> "
        f"(umbral {settings.UMBRAL_DESPERDICIO_PORCENTAJE}%)<br/>"
        f"Tickets: <b>{len(ventas)}</b>"
    )

    # Por restaurante
    rests = sesion.query(Restaurante).all()
    df_rest = []
    for r in rests:
        v_r = sum(float(v.total or 0) for v in ventas
                   if v.id_restaurante == r.id_restaurante)
        d_r = sum(float(d.costo_estimado or 0) for d in desp
                   if d.id_restaurante == r.id_restaurante)
        df_rest.append({
            "Restaurante": r.nombre_comercial,
            "Distrito": r.distrito or "",
            "Ventas": formato_moneda(v_r),
            "Desperdicio": formato_moneda(d_r),
            "% Desp.": f"{(d_r/v_r*100 if v_r>0 else 0):.2f}%",
        })
    if df_rest:
        elementos.append(Paragraph("Comparación entre restaurantes",
                                     _estilos()["SubSIGPDA"]))
        elementos.append(_tabla(pd.DataFrame(df_rest)))

    # Top platos
    detalles = sesion.query(DetalleVenta).join(Venta).filter(
        Venta.fecha >= hace_30, Venta.fecha <= hoy
    ).all()
    top = {}
    for d in detalles:
        pl = sesion.query(Plato).filter(Plato.id_plato == d.id_plato).first()
        if pl:
            top[pl.nombre] = top.get(pl.nombre, 0) + d.cantidad
    if top:
        df_top = pd.DataFrame([{"Plato": k, "Unidades": v}
                                for k, v in top.items()])\
            .sort_values("Unidades", ascending=False).head(10)
        elementos.append(Spacer(1, 0.5 * cm))
        elementos.append(Paragraph("Top 10 platos vendidos (30 días)",
                                     _estilos()["SubSIGPDA"]))
        elementos.append(_tabla(df_top))

    sesion.close()
    return _construir_pdf(elementos)


def reporte_auditoria_bitacora(fecha_ini: date | None = None,
                                  fecha_fin: date | None = None) -> bytes:
    fecha_fin = fecha_fin or date.today()
    fecha_ini = fecha_ini or (fecha_fin - timedelta(days=7))
    sesion = obtener_sesion()
    elementos = _encabezado(
        f"Reporte de Auditoría / Bitácora ({fecha_ini} - {fecha_fin})",
        _usuario_actual()
    )

    eventos = sesion.query(Bitacora).filter(
        Bitacora.fecha >= fecha_ini, Bitacora.fecha <= fecha_fin
    ).order_by(Bitacora.fecha.desc(), Bitacora.hora.desc()).limit(500).all()

    elementos += _resumen(
        f"Total de eventos en el rango: <b>{len(eventos)}</b>"
    )

    df = pd.DataFrame([{
        "Fecha": e.fecha,
        "Hora": e.hora,
        "Usuario": e.usuario_nombre or "",
        "Rol": e.rol or "",
        "Módulo": e.modulo,
        "Acción": e.accion,
        "Resultado": e.resultado,
        "IP": e.ip_equipo or "",
    } for e in eventos])
    elementos.append(_tabla(df, max_filas=200))

    sesion.close()
    return _construir_pdf(elementos)


# ----------------------------------------------------------------
# VISTA STREAMLIT
# ----------------------------------------------------------------
# Las funciones de reporte retornan bytes (PDF) para ser servidos
# como respuestas HTTP por el backend FastAPI.
