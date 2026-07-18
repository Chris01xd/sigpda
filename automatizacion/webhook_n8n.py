"""
=================================================================
SIGPDA - Cliente de Webhooks para n8n
=================================================================
Envía alertas y reportes al webhook configurado en n8n.
Si el servicio no está disponible registra el evento sin fallar
y guarda la alerta en la tabla `alertas` para reintentos manuales.
"""

from datetime import datetime
import json

import requests

from config import settings
from database import obtener_sesion
from database.modelos import Alerta


TIMEOUT_SEGUNDOS = 5


def _enviar(payload: dict) -> tuple[bool, str]:
    """Envía un payload al webhook de n8n y devuelve (exito, mensaje)."""
    if not settings.N8N_HABILITADO:
        return False, "n8n deshabilitado por configuración"

    url = settings.N8N_WEBHOOK_URL
    try:
        respuesta = requests.post(
            url,
            json=payload,
            timeout=TIMEOUT_SEGUNDOS,
            headers={"Content-Type": "application/json"},
        )
        if respuesta.status_code in (200, 201, 202):
            return True, f"Enviado correctamente (HTTP {respuesta.status_code})"
        return False, f"Respuesta inesperada: HTTP {respuesta.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"No se pudo conectar a {url}"
    except requests.exceptions.Timeout:
        return False, "Timeout al conectar con n8n"
    except Exception as e:
        return False, f"Error: {e}"


def _registrar_alerta(tipo: str, titulo: str, mensaje: str, severidad: str,
                       enviado: bool, id_restaurante: int | None = None) -> None:
    """Persiste la alerta en BD para auditoría y reenvío posterior."""
    try:
        sesion = obtener_sesion()
        alerta = Alerta(
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            severidad=severidad,
            enviado_n8n=enviado,
            fecha_envio=datetime.utcnow() if enviado else None,
            id_restaurante=id_restaurante,
        )
        sesion.add(alerta)
        sesion.commit()
        sesion.close()
    except Exception:
        # No bloquear el flujo si la tabla no está disponible.
        pass


# ----------------------------------------------------------------
# ALERTAS ESPECÍFICAS
# ----------------------------------------------------------------

def enviar_alerta_vencimiento(payload: dict) -> tuple[bool, str]:
    """
    Alerta para insumos próximos a vencer / vencidos / con bajo stock.
    `payload` debe incluir lista de insumos con sus datos.
    """
    payload_completo = {
        "tipo": "alerta_vencimiento",
        "sistema": settings.NOMBRE_SISTEMA,
        "fecha": datetime.utcnow().isoformat(),
        "severidad": "advertencia",
        **payload,
    }
    exito, mensaje = _enviar(payload_completo)
    titulo = "Insumos por vencer / con bajo stock"
    contenido = json.dumps(payload, ensure_ascii=False, default=str)[:1000]
    _registrar_alerta("vencimiento", titulo, contenido, "advertencia", exito)
    return exito, mensaje


def enviar_alerta_desperdicio(porcentaje: float, total_desperdicio: float,
                                total_ventas: float) -> tuple[bool, str]:
    """Alerta cuando el % de desperdicio supera el umbral configurado."""
    payload = {
        "tipo": "alerta_desperdicio",
        "sistema": settings.NOMBRE_SISTEMA,
        "fecha": datetime.utcnow().isoformat(),
        "severidad": "critica",
        "porcentaje_desperdicio": round(porcentaje, 2),
        "umbral_permitido": settings.UMBRAL_DESPERDICIO_PORCENTAJE,
        "total_desperdicio_costo": round(total_desperdicio, 2),
        "total_ventas": round(total_ventas, 2),
        "moneda": settings.MONEDA,
        "mensaje": (
            f"El desperdicio alcanzó {porcentaje:.2f}% superando el umbral "
            f"permitido de {settings.UMBRAL_DESPERDICIO_PORCENTAJE}%."
        ),
    }
    exito, mensaje = _enviar(payload)
    _registrar_alerta(
        "desperdicio",
        f"Desperdicio crítico: {porcentaje:.2f}%",
        payload["mensaje"],
        "critica",
        exito,
    )
    return exito, mensaje


def enviar_alerta_sobreproduccion(plato_nombre: str, resultados: list) -> tuple[bool, str]:
    """Alerta cuando la IA detecta riesgo alto de sobreproducción."""
    # Convertir fechas a string para que sean JSON serializables
    resultados_ok = [
        {**r, "fecha": str(r["fecha"])} for r in resultados
    ]
    payload = {
        "tipo": "alerta_sobreproduccion",
        "sistema": settings.NOMBRE_SISTEMA,
        "fecha": datetime.utcnow().isoformat(),
        "severidad": "advertencia",
        "plato": plato_nombre,
        "predicciones": resultados_ok,
        "mensaje": (
            f"Riesgo de sobreproducción detectado para el plato '{plato_nombre}'. "
            "Revise la recomendación de producción del módulo de IA."
        ),
    }
    exito, mensaje = _enviar(payload)
    _registrar_alerta(
        "sobreproduccion",
        f"Sobreproducción: {plato_nombre}",
        payload["mensaje"],
        "advertencia",
        exito,
    )
    return exito, mensaje


def enviar_reporte_diario(resumen: dict) -> tuple[bool, str]:
    """Envía un resumen operativo diario a n8n."""
    payload = {
        "tipo": "reporte_diario",
        "sistema": settings.NOMBRE_SISTEMA,
        "fecha": datetime.utcnow().isoformat(),
        "severidad": "info",
        "resumen": resumen,
    }
    exito, mensaje = _enviar(payload)
    _registrar_alerta("reporte_diario", "Reporte diario",
                       json.dumps(resumen, ensure_ascii=False, default=str)[:1000],
                       "info", exito)
    return exito, mensaje


def enviar_reporte_semanal(resumen: dict) -> tuple[bool, str]:
    """Envía un consolidado semanal al administrador vía n8n."""
    payload = {
        "tipo": "reporte_semanal",
        "sistema": settings.NOMBRE_SISTEMA,
        "fecha": datetime.utcnow().isoformat(),
        "severidad": "info",
        "resumen": resumen,
    }
    exito, mensaje = _enviar(payload)
    _registrar_alerta("reporte_semanal", "Reporte semanal",
                       json.dumps(resumen, ensure_ascii=False, default=str)[:1000],
                       "info", exito)
    return exito, mensaje


def enviar_alerta_personalizada(tipo: str, titulo: str, mensaje: str,
                                  severidad: str = "info",
                                  datos: dict | None = None) -> tuple[bool, str]:
    """Envía una alerta personalizada a n8n."""
    payload = {
        "tipo": tipo,
        "sistema": settings.NOMBRE_SISTEMA,
        "fecha": datetime.utcnow().isoformat(),
        "titulo": titulo,
        "mensaje": mensaje,
        "severidad": severidad,
        "datos": datos or {},
    }
    exito, msg = _enviar(payload)
    _registrar_alerta(tipo, titulo, mensaje, severidad, exito)
    return exito, msg


def probar_conexion() -> tuple[bool, str]:
    """Verifica la conectividad con el webhook de n8n."""
    payload = {
        "tipo": "ping",
        "sistema": settings.NOMBRE_SISTEMA,
        "fecha": datetime.utcnow().isoformat(),
        "mensaje": "Prueba de conectividad desde SIGPDA",
    }
    return _enviar(payload)