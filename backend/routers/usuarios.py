from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database.conexion import obtener_sesion
from database.modelos import Usuario, Rol
from utils.seguridad import hashear_contrasena
from backend.auth import obtener_usuario_actual

router = APIRouter()


class UsuarioCreate(BaseModel):
    nombre: str
    apellido: str
    correo: str
    usuario: str
    contrasena: str
    id_rol: int
    estado: bool = True


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    correo: Optional[str] = None
    id_rol: Optional[int] = None
    estado: Optional[bool] = None
    nueva_contrasena: Optional[str] = None


def _usuario_dict(u: Usuario) -> dict:
    return {
        "id_usuario": u.id_usuario,
        "nombre": u.nombre,
        "apellido": u.apellido,
        "correo": u.correo,
        "usuario": u.usuario,
        "id_rol": u.id_rol,
        "rol": u.rol.nombre if u.rol else "",
        "estado": u.estado,
        "fecha_creacion": u.fecha_creacion.isoformat() if u.fecha_creacion else None,
        "ultimo_acceso": u.ultimo_acceso.isoformat() if u.ultimo_acceso else None,
    }


@router.get("/")
def listar(current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        usuarios = sesion.query(Usuario).all()
        return [_usuario_dict(u) for u in usuarios]
    finally:
        sesion.close()


@router.post("/")
def crear(data: UsuarioCreate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        existente = sesion.query(Usuario).filter(
            (Usuario.usuario == data.usuario) | (Usuario.correo == data.correo)
        ).first()
        if existente:
            raise HTTPException(400, "Usuario o correo ya existe")

        u = Usuario(
            nombre=data.nombre,
            apellido=data.apellido,
            correo=data.correo,
            usuario=data.usuario,
            contrasena=hashear_contrasena(data.contrasena),
            id_rol=data.id_rol,
            estado=data.estado,
        )
        sesion.add(u)
        sesion.commit()
        sesion.refresh(u)
        return _usuario_dict(u)
    finally:
        sesion.close()


@router.put("/{id_usuario}")
def actualizar(id_usuario: int, data: UsuarioUpdate, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        u = sesion.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
        if not u:
            raise HTTPException(404, "Usuario no encontrado")
        if data.nombre is not None:
            u.nombre = data.nombre
        if data.apellido is not None:
            u.apellido = data.apellido
        if data.correo is not None:
            u.correo = data.correo
        if data.id_rol is not None:
            u.id_rol = data.id_rol
        if data.estado is not None:
            u.estado = data.estado
        if data.nueva_contrasena:
            u.contrasena = hashear_contrasena(data.nueva_contrasena)
        sesion.commit()
        sesion.refresh(u)
        return _usuario_dict(u)
    finally:
        sesion.close()


@router.delete("/{id_usuario}")
def eliminar(id_usuario: int, current_user: dict = Depends(obtener_usuario_actual)):
    sesion = obtener_sesion()
    try:
        u = sesion.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
        if not u:
            raise HTTPException(404, "Usuario no encontrado")
        sesion.delete(u)
        sesion.commit()
        return {"message": "Eliminado"}
    finally:
        sesion.close()
