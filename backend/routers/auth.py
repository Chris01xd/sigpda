from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime

from database.conexion import obtener_sesion
from database.modelos import Usuario, Sesion
from utils.seguridad import verificar_contrasena, obtener_ip_local
from backend.auth import crear_token, obtener_usuario_actual
from config.settings import PERMISOS_POR_ROL

router = APIRouter()


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: dict


@router.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    sesion = obtener_sesion()
    try:
        usuario = sesion.query(Usuario).filter(
            Usuario.usuario == form_data.username,
            Usuario.estado == True,
        ).first()

        if not usuario or not verificar_contrasena(form_data.password, usuario.contrasena):
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

        usuario.ultimo_acceso = datetime.utcnow()

        nueva_sesion = Sesion(
            id_usuario=usuario.id_usuario,
            ip_equipo=obtener_ip_local(),
            estado="activa",
        )
        sesion.add(nueva_sesion)
        sesion.commit()
        sesion.refresh(nueva_sesion)

        token_data = {
            "sub": str(usuario.id_usuario),
            "usuario": usuario.usuario,
            "nombre": f"{usuario.nombre} {usuario.apellido}",
            "rol": usuario.rol.nombre,
            "id_sesion": nueva_sesion.id_sesion,
        }
        token = crear_token(token_data)

        permisos = PERMISOS_POR_ROL.get(usuario.rol.nombre, {})

        return {
            "access_token": token,
            "token_type": "bearer",
            "usuario": {
                "id": usuario.id_usuario,
                "nombre": usuario.nombre,
                "apellido": usuario.apellido,
                "usuario": usuario.usuario,
                "correo": usuario.correo,
                "rol": usuario.rol.nombre,
                "permisos": permisos,
            },
        }
    finally:
        sesion.close()


@router.post("/logout")
def logout(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        id_sesion = current_user.get("id_sesion")
        if id_sesion:
            s = sesion.query(Sesion).filter(Sesion.id_sesion == id_sesion).first()
            if s:
                s.estado = "cerrada"
                s.fecha_salida = datetime.utcnow()
                sesion.commit()
    finally:
        sesion.close()
    return {"message": "Sesión cerrada"}


@router.get("/me")
def get_me(current_user: dict = Depends(obtener_usuario_actual)):
    return current_user
