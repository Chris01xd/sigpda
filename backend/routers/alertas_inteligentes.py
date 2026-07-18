from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.auth import obtener_usuario_actual
from database.conexion import obtener_sesion
from database.modelos import AlertaInteligente
from backend.services.alertas_inteligentes import (
    generar_alertas_inteligentes,
    obtener_alertas_activas,
)
from backend.services.notificaciones import enviar_notificaciones

router = APIRouter()


class GenerarAlertasRequest(BaseModel):
    clima: int  = Field(default=2, ge=1, le=3)
    evento: int = Field(default=0, ge=0, le=2)


@router.get("/")
def listar_alertas(
    limit: int  = Query(default=50, ge=1, le=200),
    tipo:  str  = Query(default=None),
    nivel: str  = Query(default=None),
    estado: str = Query(default="pendiente"),
    current_user: dict = Depends(obtener_usuario_actual),
):
    return obtener_alertas_activas(limit=limit, tipo=tipo, nivel=nivel, estado=estado)


@router.post("/generar")
def generar(
    data: GenerarAlertasRequest,
    current_user: dict = Depends(obtener_usuario_actual),
):
    resultado = generar_alertas_inteligentes(clima=data.clima, evento=data.evento)
    nuevas = resultado.get("alertas", [])

    if nuevas:
        # Hay alertas nuevas: notificar solo las nuevas
        enviar_notificaciones(nuevas)
    else:
        # Sin nuevas (deduplicación): notificar con todas las pendientes existentes
        pendientes = obtener_alertas_activas(limit=200, estado="pendiente")
        if pendientes:
            payload = [{"tipo": a["tipo_alerta"], "nivel": a["nivel_riesgo"]} for a in pendientes]
            enviar_notificaciones(payload)

    return resultado


@router.put("/{id_alerta}/marcar-leida")
def marcar_leida(
    id_alerta: int,
    current_user: dict = Depends(obtener_usuario_actual),
):
    sesion = obtener_sesion()
    try:
        alerta = sesion.query(AlertaInteligente).filter(
            AlertaInteligente.id_alerta == id_alerta
        ).first()
        if not alerta:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        alerta.estado = "leida"
        sesion.commit()
        return {"ok": True, "estado": "leida"}
    except HTTPException:
        raise
    except Exception as e:
        sesion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        sesion.close()


@router.put("/{id_alerta}/resolver")
def resolver(
    id_alerta: int,
    current_user: dict = Depends(obtener_usuario_actual),
):
    sesion = obtener_sesion()
    try:
        alerta = sesion.query(AlertaInteligente).filter(
            AlertaInteligente.id_alerta == id_alerta
        ).first()
        if not alerta:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        alerta.estado = "resuelta"
        sesion.commit()
        return {"ok": True, "estado": "resuelta"}
    except HTTPException:
        raise
    except Exception as e:
        sesion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        sesion.close()
