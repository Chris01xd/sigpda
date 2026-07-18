"""Paquete de automatización con n8n."""
from .webhook_n8n import (
    enviar_alerta_vencimiento,
    enviar_alerta_desperdicio,
    enviar_alerta_sobreproduccion,
    enviar_reporte_diario,
    enviar_reporte_semanal,
    enviar_alerta_personalizada,
    probar_conexion,
)
