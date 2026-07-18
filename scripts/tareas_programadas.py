# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
"""
=================================================================
SIGPDA - Tareas Programadas
=================================================================
Consulta la BD (SQLite o PostgreSQL) y envía reportes reales a n8n.
Ejecutar manualmente o con el scheduler de Windows/Linux.

Uso:
    python -m scripts.tareas_programadas diario
    python -m scripts.tareas_programadas semanal
"""

import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import obtener_sesion
from database.modelos import Venta, DetalleVenta, Desperdicio, Plato
from automatizacion.webhook_n8n import enviar_reporte_diario, enviar_reporte_semanal
from utils.helpers import formato_moneda
from sqlalchemy import func


def _obtener_resumen_diario(fecha_obj: date) -> dict:
    """Consulta la BD y arma el resumen del día."""
    sesion = obtener_sesion()
    try:
        # Ventas del día
        ventas = sesion.query(Venta).filter(Venta.fecha == fecha_obj).all()
        total_ventas = sum(float(v.total or 0) for v in ventas)
        tickets = len(ventas)

        # Desperdicio del día
        desperdicios = sesion.query(Desperdicio).filter(
            Desperdicio.fecha == fecha_obj
        ).all()
        total_desp_costo = sum(float(d.costo_estimado or 0) for d in desperdicios)
        total_desp_cant = sum(float(d.cantidad or 0) for d in desperdicios)
        pct_desp = (total_desp_costo / total_ventas * 100) if total_ventas > 0 else 0

        # Top plato del día
        detalles = sesion.query(DetalleVenta).join(Venta).filter(
            Venta.fecha == fecha_obj
        ).all()
        top_platos = {}
        for d in detalles:
            plato = sesion.query(Plato).filter(
                Plato.id_plato == d.id_plato
            ).first()
            if plato:
                top_platos[plato.nombre] = top_platos.get(plato.nombre, 0) + d.cantidad
        top_plato = max(top_platos, key=top_platos.get) if top_platos else "Sin ventas"

        return {
            "ventas_total": round(total_ventas, 2),
            "tickets": tickets,
            "platos_vendidos": sum(top_platos.values()),
            "desperdicio_total": round(total_desp_costo, 2),
            "desperdicio_cantidad": round(total_desp_cant, 2),
            "porcentaje_desperdicio": round(pct_desp, 2),
            "top_plato": top_plato,
            "estado": "OK - Bajo control" if pct_desp < 15 else "ALERTA - Supera umbral",
        }
    finally:
        sesion.close()


def _obtener_resumen_semanal(fecha_fin: date) -> dict:
    """Consulta la BD y arma el resumen semanal."""
    fecha_ini = fecha_fin - timedelta(days=6)
    sesion = obtener_sesion()
    try:
        ventas = sesion.query(Venta).filter(
            Venta.fecha >= fecha_ini, Venta.fecha <= fecha_fin
        ).all()
        total_ventas = sum(float(v.total or 0) for v in ventas)
        tickets = len(ventas)
        promedio_diario = total_ventas / 7

        desperdicios = sesion.query(Desperdicio).filter(
            Desperdicio.fecha >= fecha_ini, Desperdicio.fecha <= fecha_fin
        ).all()
        total_desp = sum(float(d.costo_estimado or 0) for d in desperdicios)
        pct_desp = (total_desp / total_ventas * 100) if total_ventas > 0 else 0

        # Top 5 platos
        detalles = sesion.query(DetalleVenta).join(Venta).filter(
            Venta.fecha >= fecha_ini, Venta.fecha <= fecha_fin
        ).all()
        top_platos = {}
        for d in detalles:
            plato = sesion.query(Plato).filter(
                Plato.id_plato == d.id_plato
            ).first()
            if plato:
                top_platos[plato.nombre] = top_platos.get(plato.nombre, 0) + d.cantidad
        top_5 = sorted(top_platos.items(), key=lambda x: x[1], reverse=True)[:5]
        top_5_str = ", ".join([f"{n}: {c} und." for n, c in top_5])

        # Motivos de desperdicio
        motivos = {}
        for d in desperdicios:
            motivos[d.motivo] = motivos.get(d.motivo, 0) + 1
        motivos_str = ", ".join([f"{m}: {c}" for m, c in
                                  sorted(motivos.items(), key=lambda x: x[1], reverse=True)[:3]])

        return {
            "periodo": f"{fecha_ini} al {fecha_fin}",
            "ventas_semana": round(total_ventas, 2),
            "tickets_semana": tickets,
            "promedio_diario": round(promedio_diario, 2),
            "desperdicio_semana": round(total_desp, 2),
            "porcentaje_desperdicio": round(pct_desp, 2),
            "top_5_platos": top_5_str or "Sin datos",
            "motivos_principales": motivos_str or "Sin datos",
            "estado": "OK - Bajo control" if pct_desp < 15 else "ALERTA - Supera umbral",
        }
    finally:
        sesion.close()


def ejecutar_reporte_diario():
    hoy = date.today()
    print(f"[SIGPDA] Generando reporte diario para {hoy}...")
    resumen = _obtener_resumen_diario(hoy)
    print(f"[SIGPDA] Resumen: {resumen}")
    exito, mensaje = enviar_reporte_diario(resumen)
    if exito:
        print(f"[SIGPDA] OK Reporte diario enviado: {mensaje}")
    else:
        print(f"[SIGPDA] ERROR Error enviando reporte: {mensaje}")
    return exito


def ejecutar_reporte_semanal():
    hoy = date.today()
    print(f"[SIGPDA] Generando reporte semanal hasta {hoy}...")
    resumen = _obtener_resumen_semanal(hoy)
    print(f"[SIGPDA] Resumen: {resumen}")
    exito, mensaje = enviar_reporte_semanal(resumen)
    if exito:
        print(f"[SIGPDA] OK Reporte semanal enviado: {mensaje}")
    else:
        print(f"[SIGPDA] ERROR Error enviando reporte: {mensaje}")
    return exito


if __name__ == "__main__":
    tipo = sys.argv[1] if len(sys.argv) > 1 else "diario"
    if tipo == "diario":
        ejecutar_reporte_diario()
    elif tipo == "semanal":
        ejecutar_reporte_semanal()
    else:
        print("Uso: python -m scripts.tareas_programadas [diario|semanal]")