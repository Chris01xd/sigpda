"""
=================================================================
SIGPDA - Utilidades de Seguridad
=================================================================
Funciones para cifrado de contraseñas e IP.
"""

import socket
import bcrypt


def hashear_contrasena(contrasena: str) -> str:
    sal = bcrypt.gensalt()
    return bcrypt.hashpw(contrasena.encode("utf-8"), sal).decode("utf-8")


def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(
            contrasena.encode("utf-8"),
            hash_guardado.encode("utf-8")
        )
    except Exception:
        return False


def obtener_ip_local() -> str:
    try:
        nombre_host = socket.gethostname()
        return socket.gethostbyname(nombre_host)
    except Exception:
        return "127.0.0.1"
