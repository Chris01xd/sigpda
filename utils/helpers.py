"""
=================================================================
SIGPDA - Helpers generales
=================================================================
"""

from datetime import datetime
from config.settings import MONEDA


def formato_moneda(valor) -> str:
    try:
        return f"{MONEDA} {float(valor):,.2f}"
    except Exception:
        return f"{MONEDA} 0.00"


def formato_fecha(fecha) -> str:
    if not fecha:
        return "-"
    if isinstance(fecha, str):
        return fecha
    try:
        return fecha.strftime("%d/%m/%Y")
    except Exception:
        return str(fecha)


def formato_fecha_hora(fecha) -> str:
    if not fecha:
        return "-"
    try:
        return fecha.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(fecha)


def hora_actual() -> str:
    return datetime.utcnow().strftime("%H:%M:%S")


def dia_semana_es(fecha) -> str:
    nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    return nombres[fecha.weekday()]


def mes_es(numero_mes: int) -> str:
    nombres = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    return nombres[numero_mes - 1] if 1 <= numero_mes <= 12 else "-"
