"""
SIGPDA - Exportador de datos a Excel y CSV
Retorna BytesIO / bytes para ser servidos como respuestas HTTP.
"""

from io import BytesIO
from datetime import datetime

import pandas as pd


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def generar_excel(df: pd.DataFrame, nombre: str) -> tuple[BytesIO, str]:
    """Genera un archivo Excel y retorna (buffer, filename)."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")
    buffer.seek(0)
    return buffer, f"{nombre}_{_timestamp()}.xlsx"


def generar_csv(df: pd.DataFrame, nombre: str) -> tuple[bytes, str]:
    """Genera CSV y retorna (bytes, filename)."""
    data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    return data, f"{nombre}_{_timestamp()}.csv"


def generar_excel_multihoja(hojas: dict, nombre: str) -> tuple[BytesIO, str]:
    """Genera Excel con múltiples hojas y retorna (buffer, filename)."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for nombre_hoja, df in hojas.items():
            if df is None or df.empty:
                pd.DataFrame({"info": ["Sin datos"]}).to_excel(writer, index=False, sheet_name=nombre_hoja[:31])
            else:
                df.to_excel(writer, index=False, sheet_name=nombre_hoja[:31])
    buffer.seek(0)
    return buffer, f"{nombre}_{_timestamp()}.xlsx"
