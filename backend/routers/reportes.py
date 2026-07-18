"""
Generador de reporte PDF semanal para SIGPDA.
Usa fpdf2 (instalado en requirements.txt como fpdf2==2.7.7).
"""
from __future__ import annotations
import io
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fpdf import FPDF
from sqlalchemy import func

from backend.auth import obtener_usuario_actual
from backend.services.huella_carbono import calcular_huella, calcular_ahorro
from backend.services.alertas_inteligentes import obtener_alertas_activas
from database.conexion import obtener_sesion
from database.modelos import Desperdicio, Plato

router = APIRouter()

# ---- Colores corporativos ----
_MORADO  = (99,  102, 241)
_ROJO    = (220,  38,  38)
_NARANJA = (234,  88,  12)
_VERDE   = (22,  163,  74)
_GRIS    = (107, 114, 128)
_GRIS_F  = (243, 244, 246)


def _n(txt: str) -> str:
    """Normaliza caracteres latinos para fpdf2 (Latin-1)."""
    return (txt
        .replace("á","a").replace("é","e").replace("í","i")
        .replace("ó","o").replace("ú","u").replace("ü","u")
        .replace("ñ","n").replace("Á","A").replace("É","E")
        .replace("Í","I").replace("Ó","O").replace("Ú","U")
        .replace("Ñ","N").replace("°","").replace("–","-")
        .replace("’","'").replace("“",'"').replace("”",'"')
    )


class _PDF(FPDF):
    def header(self):
        self.set_fill_color(*_MORADO)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(255, 255, 255)
        self.set_y(4)
        self.cell(0, 10, "SIGPDA - Reporte Semanal de Gestion del Desperdicio", align="C")
        self.set_text_color(0, 0, 0)
        self.ln(14)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*_GRIS)
        self.cell(0, 10,
            f"Sistema SIGPDA - Valle Jequetepeque 2026  |  Pag. {self.page_no()}",
            align="C")
        self.set_text_color(0, 0, 0)

    def seccion(self, titulo: str):
        self.ln(4)
        self.set_fill_color(*_MORADO)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, f"  {_n(titulo)}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def kpi_row(self, items: list[tuple[str, str, tuple]]):
        """Fila de tarjetas KPI. items = [(label, valor, color_rgb), ...]"""
        ancho = 190 / len(items)
        x0 = self.get_x()
        y0 = self.get_y()
        for label, valor, color in items:
            self.set_fill_color(*_GRIS_F)
            self.set_draw_color(*color)
            self.set_line_width(0.8)
            self.rect(x0, y0, ancho - 2, 22, "DF")
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(*color)
            self.set_xy(x0 + 1, y0 + 3)
            self.cell(ancho - 4, 8, _n(valor), align="C")
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*_GRIS)
            self.set_xy(x0 + 1, y0 + 13)
            self.cell(ancho - 4, 6, _n(label), align="C")
            x0 += ancho
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)
        self.ln(26)

    def tabla(self, encabezados: list[str], filas: list[list[str]], anchos: list[float]):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(*_MORADO)
        self.set_text_color(255, 255, 255)
        for h, w in zip(encabezados, anchos):
            self.cell(w, 7, _n(h), border=1, fill=True, align="C")
        self.ln()
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "", 8)
        for i, fila in enumerate(filas):
            self.set_fill_color(243, 244, 246) if i % 2 == 0 else self.set_fill_color(255, 255, 255)
            for celda, w in zip(fila, anchos):
                self.cell(w, 6, _n(str(celda)), border=1, fill=True)
            self.ln()
        self.ln(2)


def _generar_pdf() -> bytes:
    hoy    = date.today()
    inicio = hoy - timedelta(days=7)

    # ---- Recopilar datos ----
    huella  = calcular_huella(dias=30)
    ahorro  = calcular_ahorro(dias=30)
    alertas = obtener_alertas_activas(limit=10, estado="pendiente")

    sesion = obtener_sesion()
    try:
        top_desperdicios = (
            sesion.query(
                Plato.nombre,
                func.coalesce(func.sum(Desperdicio.cantidad), 0).label("cant"),
                func.coalesce(func.sum(Desperdicio.costo_estimado), 0).label("costo"),
            )
            .join(Plato, Desperdicio.id_plato == Plato.id_plato)
            .filter(Desperdicio.fecha >= hoy - timedelta(days=30))
            .group_by(Plato.nombre)
            .order_by(func.sum(Desperdicio.costo_estimado).desc())
            .limit(8)
            .all()
        )
        total_registros_sem = (
            sesion.query(func.count(Desperdicio.id_desperdicio))
            .filter(Desperdicio.fecha >= inicio)
            .scalar() or 0
        )
        costo_semana = float(
            sesion.query(func.coalesce(func.sum(Desperdicio.costo_estimado), 0))
            .filter(Desperdicio.fecha >= inicio)
            .scalar() or 0
        )
    finally:
        sesion.close()

    # ---- Construir PDF ----
    pdf = _PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(10, 20, 10)

    # Subtítulo / período
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_GRIS)
    pdf.cell(0, 6,
        f"Periodo: {inicio.strftime('%d/%m/%Y')} al {hoy.strftime('%d/%m/%Y')}  |  "
        f"Generado: {hoy.strftime('%d/%m/%Y')}",
        align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ---- KPIs semana ----
    pdf.seccion("Resumen de la Semana")
    pdf.kpi_row([
        ("Registros desperdicio", str(total_registros_sem),       _MORADO),
        ("Costo desperdiciado",   f"S/ {costo_semana:.2f}",       _ROJO),
        ("Alertas pendientes",    str(len(alertas)),               _NARANJA),
        ("Ahorro vs mes ant.",    f"S/ {ahorro['ahorro_periodo']:.2f}", _VERDE),
    ])

    # ---- Huella ambiental (30 días) ----
    pdf.seccion("Huella Ambiental - Ultimos 30 dias")
    pdf.kpi_row([
        ("CO2 Equivalente",    f"{huella['total_co2_kg']} kg",           _ROJO),
        ("Agua desperdiciada", f"{int(huella['total_agua_litros'])} L",  (37,99,235)),
        ("Arboles necesarios", f"{huella['equivalencias']['arboles_anuales']}", _VERDE),
        ("Km en auto equiv.",  f"{huella['equivalencias']['km_en_auto']:.0f} km", _NARANJA),
    ])

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*_GRIS)
    pdf.cell(0, 5,
        "Factores de emision FAO / Our World in Data 2023. "
        "1 arbol absorbe ~22 kg CO2/ano. Auto promedio: 0.21 kg CO2/km.",
        new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # ---- Top desperdicios ----
    if top_desperdicios:
        pdf.seccion("Top Platos con Mayor Desperdicio (30 dias)")
        filas = [
            [d.nombre, f"{float(d.cant):.1f}", f"S/ {float(d.costo):.2f}"]
            for d in top_desperdicios
        ]
        pdf.tabla(
            ["Plato", "Cantidad (und)", "Costo estimado"],
            filas,
            [110.0, 40.0, 40.0],
        )

    # ---- Huella por categoría ----
    if huella["por_categoria"]:
        pdf.seccion("Impacto Ambiental por Categoria de Alimento")
        filas_cat = [
            [c["categoria"], f"{c['kg_desperdiciado']:.2f}", f"{c['co2_kg']:.2f}", f"{int(c['agua_litros'])}"]
            for c in huella["por_categoria"][:8]
        ]
        pdf.tabla(
            ["Categoria", "Kg desperd.", "CO2 (kg)", "Agua (L)"],
            filas_cat,
            [70.0, 40.0, 40.0, 40.0],
        )

    # ---- Ahorro económico ----
    pdf.seccion("Comparativa de Ahorro Economico")
    tend = {"mejora": "MEJORA", "empeora": "EMPEORA", "igual": "SIN CAMBIO"}.get(ahorro["tendencia"], "")
    color_tend = _VERDE if ahorro["tendencia"] == "mejora" else (_ROJO if ahorro["tendencia"] == "empeora" else _GRIS)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_fill_color(*_GRIS_F)
    pdf.rect(10, pdf.get_y(), 190, 28, "F")
    y = pdf.get_y() + 3
    pdf.set_xy(14, y)
    pdf.cell(60, 6, f"Costo mes actual:    S/ {ahorro['costo_actual']:.2f}")
    pdf.set_xy(14, y + 7)
    pdf.cell(60, 6, f"Costo mes anterior:  S/ {ahorro['costo_anterior']:.2f}")
    pdf.set_xy(14, y + 14)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*color_tend)
    pdf.cell(60, 6, f"Ahorro: S/ {ahorro['ahorro_periodo']:.2f}  ({ahorro['porcentaje_mejora']:.1f}%)  -> {tend}")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(32)

    # ---- Alertas activas ----
    pdf.set_x(pdf.l_margin)
    if alertas:
        pdf.seccion("Alertas Inteligentes Activas (pendientes)")
        colores_nivel = {"CRITICO": _ROJO, "ALTO": _NARANJA, "MEDIO": (217, 119, 6), "BAJO": _VERDE}
        for a in alertas[:8]:
            color = colores_nivel.get(a["nivel_riesgo"], _GRIS)
            pdf.set_text_color(*color)
            pdf.set_font("Helvetica", "B", 8)
            linea = f"[{a['nivel_riesgo']}] {_n(a['titulo'])}"
            pdf.multi_cell(0, 6, linea, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)

    # ---- Recomendaciones de las alertas ----
    pdf.set_x(pdf.l_margin)
    recs = [a for a in alertas if a.get("recomendacion")][:4]
    if recs:
        pdf.seccion("Recomendaciones Operativas")
        for i, a in enumerate(recs, 1):
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 8)
            pdf.multi_cell(0, 5, f"{i}. {_n(a['titulo'])}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*_GRIS)
            pdf.multi_cell(0, 5, _n(a["recomendacion"]), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)

    return bytes(pdf.output())


@router.get("/semanal", response_class=StreamingResponse)
def reporte_semanal(current_user: dict = Depends(obtener_usuario_actual)):
    pdf_bytes = _generar_pdf()
    nombre = f"SIGPDA_Reporte_{date.today().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre}"},
    )


# ================================================================
# REPORTES DE EXPERIMENTACIÓN DE IA (comparación de 5 modelos)
# ================================================================
# No reemplazan el reporte semanal ni los reportes generales
# existentes (reportes/generador_pdf.py): son específicos de una
# ejecución de /ia/entrenar-comparar ya persistida en BD (Fase 7).

@router.get("/ia/{ejecucion_id}/pdf", response_class=StreamingResponse)
def reporte_ia_pdf(ejecucion_id: int, current_user: dict = Depends(obtener_usuario_actual)):
    from ia.reportes_ia import generar_pdf_ia

    contenido = generar_pdf_ia(ejecucion_id)
    if contenido is None:
        raise HTTPException(status_code=404, detail=f"No existe la ejecución de IA con ID {ejecucion_id}.")

    nombre = f"SIGPDA_IA_{ejecucion_id}_{date.today().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre}"},
    )


@router.get("/ia/{ejecucion_id}/word", response_class=StreamingResponse)
def reporte_ia_word(ejecucion_id: int, current_user: dict = Depends(obtener_usuario_actual)):
    from ia.reportes_ia import generar_word_ia

    contenido = generar_word_ia(ejecucion_id)
    if contenido is None:
        raise HTTPException(status_code=404, detail=f"No existe la ejecución de IA con ID {ejecucion_id}.")

    nombre = f"SIGPDA_IA_{ejecucion_id}_{date.today().strftime('%Y%m%d')}.docx"
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={nombre}"},
    )


@router.get("/ia/{ejecucion_id}/excel", response_class=StreamingResponse)
def reporte_ia_excel(ejecucion_id: int, current_user: dict = Depends(obtener_usuario_actual)):
    from ia.reportes_ia import generar_excel_ia

    contenido = generar_excel_ia(ejecucion_id)
    if contenido is None:
        raise HTTPException(status_code=404, detail=f"No existe la ejecución de IA con ID {ejecucion_id}.")

    nombre = f"SIGPDA_IA_{ejecucion_id}_{date.today().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={nombre}"},
    )
