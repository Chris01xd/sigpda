"""
=================================================================
SIGPDA - Validaciones
=================================================================
"""

import re


def validar_correo(correo: str) -> bool:
    patron = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(patron, correo or ""))


def validar_ruc(ruc: str) -> bool:
    """RUC peruano: 11 dígitos numéricos."""
    return bool(ruc and ruc.isdigit() and len(ruc) == 11)


def validar_telefono(telefono: str) -> bool:
    if not telefono:
        return True  # opcional
    return bool(re.match(r"^[\d\s\+\-\(\)]{6,20}$", telefono))


def validar_no_vacio(valor) -> bool:
    return bool(valor and str(valor).strip())


def validar_numero_positivo(valor) -> bool:
    try:
        return float(valor) >= 0
    except Exception:
        return False


def validar_password_fuerza(contrasena: str):
    """Devuelve (valido: bool, mensaje: str)."""
    if not contrasena or len(contrasena) < 6:
        return False, "La contraseña debe tener mínimo 6 caracteres"
    return True, "OK"
