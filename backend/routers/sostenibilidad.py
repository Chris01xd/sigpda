from fastapi import APIRouter, Depends, Query
from backend.auth import obtener_usuario_actual
from backend.services.huella_carbono import calcular_huella, calcular_ahorro

router = APIRouter()


@router.get("/huella-carbono")
def huella_carbono(
    dias: int = Query(default=30, ge=7, le=365),
    current_user: dict = Depends(obtener_usuario_actual),
):
    return calcular_huella(dias=dias)


@router.get("/ahorro-economico")
def ahorro_economico(
    dias: int = Query(default=30, ge=7, le=365),
    current_user: dict = Depends(obtener_usuario_actual),
):
    return calcular_ahorro(dias=dias)
