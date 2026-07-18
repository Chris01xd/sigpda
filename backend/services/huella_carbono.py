"""
Servicio de Huella de Carbono e Hídrica del desperdicio alimentario.
Factores de emisión basados en datos FAO / Our World in Data (2023).
"""
from __future__ import annotations
from datetime import date, timedelta
from sqlalchemy import func
from database.conexion import obtener_sesion
from database.modelos import Desperdicio, Insumo, Plato

# kg CO2 equivalente por kg de alimento
_CO2: dict[str, float] = {
    "carne": 25.0, "res": 25.0, "vacuno": 25.0, "cabrito": 20.0,
    "cordero": 20.0, "cerdo": 7.6, "pollo": 6.9, "ave": 6.9,
    "pato": 6.9, "pavo": 6.9, "pescado": 3.0, "mariscos": 3.0,
    "concha": 3.0, "camaron": 3.0, "langostino": 3.0,
    "arroz": 3.0, "fideo": 1.7, "pasta": 1.7, "pan": 1.4,
    "harina": 1.4, "verdura": 2.0, "vegetal": 2.0, "hortaliza": 2.0,
    "papa": 0.5, "yuca": 0.9, "camote": 0.9, "fruta": 1.1,
    "lacteo": 3.2, "leche": 3.2, "queso": 9.8, "huevo": 4.8,
    "aceite": 3.3, "azucar": 3.0, "legumbre": 1.8, "menestra": 1.8,
    "frijol": 1.8, "lenteja": 1.8, "sal": 0.1, "aji": 1.5,
    "cebolla": 0.5, "tomate": 1.4, "ajo": 0.5, "limon": 0.9,
}

# Litros de agua por kg de alimento
_AGUA: dict[str, float] = {
    "carne": 15400.0, "res": 15400.0, "vacuno": 15400.0,
    "cabrito": 10400.0, "cordero": 10400.0, "cerdo": 5990.0,
    "pollo": 4300.0, "ave": 4300.0, "pato": 4300.0,
    "pescado": 590.0, "mariscos": 590.0, "concha": 590.0,
    "arroz": 2500.0, "fideo": 1850.0, "pasta": 1850.0,
    "pan": 1600.0, "harina": 1600.0, "verdura": 322.0,
    "vegetal": 322.0, "papa": 287.0, "yuca": 500.0,
    "fruta": 962.0, "lacteo": 1000.0, "leche": 1000.0,
    "queso": 3178.0, "huevo": 3300.0, "aceite": 4000.0,
    "azucar": 1780.0, "legumbre": 4055.0, "menestra": 4055.0,
    "frijol": 4055.0, "lenteja": 4055.0, "cebolla": 272.0,
    "tomate": 214.0, "ajo": 379.0,
}

_DEF_CO2  = 2.5
_DEF_AGUA = 1000.0


def _buscar(nombre: str, tabla: dict[str, float], default: float) -> float:
    n = nombre.lower()
    # Normalizar tildes para busqueda
    for rep, car in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")]:
        n = n.replace(rep, car)
    for clave, val in tabla.items():
        if clave in n:
            return val
    return default


def _a_kg(cantidad: float, unidad: str) -> float:
    u = (unidad or "").lower().strip()
    if u in ("g", "gr", "gramo", "gramos"):
        return cantidad / 1000
    if u in ("ml", "mililitro", "mililitros"):
        return cantidad / 1000
    return cantidad  # asumir kg o L (densidad ~1)


def calcular_huella(dias: int = 30) -> dict:
    sesion = obtener_sesion()
    try:
        desde = date.today() - timedelta(days=dias)
        rows = (
            sesion.query(
                Desperdicio.cantidad,
                Desperdicio.unidad_medida,
                Desperdicio.costo_estimado,
                Insumo.nombre.label("nom_insumo"),
                Insumo.categoria.label("cat_insumo"),
                Plato.nombre.label("nom_plato"),
                Plato.categoria.label("cat_plato"),
            )
            .outerjoin(Insumo, Desperdicio.id_insumo == Insumo.id_insumo)
            .outerjoin(Plato,  Desperdicio.id_plato  == Plato.id_plato)
            .filter(Desperdicio.fecha >= desde)
            .all()
        )
    finally:
        sesion.close()

    total_co2 = total_agua = total_kg = total_costo = 0.0
    por_cat: dict[str, dict] = {}

    for r in rows:
        nombre = r.nom_insumo or r.nom_plato or "Otros"
        cat    = r.cat_insumo or r.cat_plato or nombre
        kg     = _a_kg(float(r.cantidad or 0), r.unidad_medida or "kg")
        co2    = kg * _buscar(nombre, _CO2,  _DEF_CO2)
        agua   = kg * _buscar(nombre, _AGUA, _DEF_AGUA)
        costo  = float(r.costo_estimado or 0)

        total_co2   += co2
        total_agua  += agua
        total_kg    += kg
        total_costo += costo

        k = cat.title()
        if k not in por_cat:
            por_cat[k] = {"co2_kg": 0.0, "agua_litros": 0.0, "kg_desperdiciado": 0.0, "costo": 0.0}
        por_cat[k]["co2_kg"]          += co2
        por_cat[k]["agua_litros"]     += agua
        por_cat[k]["kg_desperdiciado"] += kg
        por_cat[k]["costo"]           += costo

    for v in por_cat.values():
        v["co2_kg"]          = round(v["co2_kg"], 2)
        v["agua_litros"]     = round(v["agua_litros"], 0)
        v["kg_desperdiciado"] = round(v["kg_desperdiciado"], 3)
        v["costo"]           = round(v["costo"], 2)

    return {
        "periodo_dias":           dias,
        "total_co2_kg":           round(total_co2,   2),
        "total_agua_litros":      round(total_agua,   0),
        "total_kg_desperdiciado": round(total_kg,     3),
        "total_costo_soles":      round(total_costo,  2),
        "equivalencias": {
            "arboles_anuales": round(total_co2 / 22,   1),   # 1 árbol absorbe ~22 kg CO2/año
            "km_en_auto":      round(total_co2 / 0.21, 1),   # ~0.21 kg CO2/km promedio
            "duchas_perdidas": round(total_agua / 65,  0),   # ~65 L por ducha de 8 min
        },
        "por_categoria": sorted(
            [{"categoria": k, **v} for k, v in por_cat.items()],
            key=lambda x: -x["co2_kg"],
        ),
    }


def calcular_ahorro(dias: int = 30) -> dict:
    sesion = obtener_sesion()
    try:
        hoy      = date.today()
        ini_act  = hoy - timedelta(days=dias)
        ini_ant  = hoy - timedelta(days=dias * 2)

        def _costo(desde, hasta=None):
            q = sesion.query(func.coalesce(func.sum(Desperdicio.costo_estimado), 0))
            q = q.filter(Desperdicio.fecha >= desde)
            if hasta:
                q = q.filter(Desperdicio.fecha < hasta)
            return float(q.scalar() or 0)

        actual    = _costo(ini_act)
        anterior  = _costo(ini_ant, ini_act)
        historico = _costo(date(2020, 1, 1))
    finally:
        sesion.close()

    ahorro = anterior - actual
    pct    = (ahorro / anterior * 100) if anterior > 0 else 0.0

    return {
        "periodo_dias":            dias,
        "costo_actual":            round(actual,    2),
        "costo_anterior":          round(anterior,  2),
        "ahorro_periodo":          round(ahorro,    2),
        "porcentaje_mejora":       round(pct,       1),
        "total_historico":         round(historico, 2),
        "tendencia": "mejora" if ahorro > 0 else ("igual" if ahorro == 0 else "empeora"),
    }
