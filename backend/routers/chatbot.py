import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from datetime import date

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from backend.auth import obtener_usuario_actual
from config.settings import GEMINI_API_KEY, CHATBOT_MODEL, CHATBOT_MAX_TOKENS
from database.conexion import obtener_sesion
from database.modelos import Desperdicio, Venta, Plato, Restaurante

router = APIRouter()
logger = logging.getLogger("sigpda.chatbot")

MAX_MENSAJE_CHARS = 2000
MAX_TURNOS_HISTORIAL = 12

SYSTEM_PROMPT_BASE = """Eres el asistente virtual de SIGPDA (Sistema Inteligente de Gestión y \
Predicción de Desperdicio Alimentario), un sistema usado por restaurantes y pequeñas y \
medianas empresas (PyMEs) gastronómicas para reducir el desperdicio de alimentos y mejorar \
sus decisiones de compra, producción y ventas.

Tu único propósito es ayudar con temas relacionados a:
- Gestión y reducción de desperdicio alimentario.
- Ventas, producción, insumos, recetas y platos del restaurante.
- Predicción de demanda, estadísticas y reportes del sistema.
- Uso y navegación del sistema SIGPDA (dónde encontrar cada función, cómo interpretar \
  gráficos y reportes).
- Buenas prácticas generales de gestión de restaurantes/PyMEs relacionadas a sostenibilidad \
  y control de desperdicio.

Si te preguntan algo totalmente ajeno a estos temas (por ejemplo, temas personales, \
entretenimiento, programación general no relacionada al sistema, etc.), responde con \
amabilidad que tu función es exclusivamente ayudar con la gestión de desperdicio y \
operación del restaurante en SIGPDA, y ofrece redirigir la conversación a esos temas.

Sé breve, claro y concreto (evita respuestas largas salvo que el usuario pida detalle). \
No inventes datos numéricos específicos del negocio que no se te hayan proporcionado en \
el contexto de esta conversación; si no tienes el dato, indícalo y sugiere en qué módulo \
del sistema puede consultarlo."""

IDIOMAS_SOPORTADOS = ("es", "en", "zh")

INSTRUCCION_IDIOMA = {
    "es": "Responde siempre en español, sin importar el idioma del mensaje del usuario.",
    "en": "Always respond in English, regardless of the language of the user's message.",
    "zh": "请始终使用简体中文回答，无论用户消息使用什么语言。",
}

MENSAJE_RECHAZO = {
    "es": "No puedo responder a eso. ¿Puedo ayudarte con algo relacionado a la gestión de desperdicio o al sistema SIGPDA?",
    "en": "I can't answer that. Can I help you with something related to waste management or the SIGPDA system?",
    "zh": "我无法回答这个问题。我可以帮你解答与浪费管理或 SIGPDA 系统相关的问题吗？",
}

MENSAJE_RESPUESTA_VACIA = {
    "es": "No obtuve una respuesta clara. ¿Puedes reformular tu pregunta?",
    "en": "I didn't get a clear answer. Could you rephrase your question?",
    "zh": "我没有得到明确的答案，能否换个方式提问？",
}

# Finish reasons de Gemini que indican que el modelo sí generó una respuesta normal.
FINISH_REASONS_OK = {"STOP", "MAX_TOKENS"}


def _idioma_valido(idioma: str | None) -> str:
    return idioma if idioma in IDIOMAS_SOPORTADOS else "es"


class MensajeChatEntrada(BaseModel):
    mensaje: str = Field(..., min_length=1, max_length=MAX_MENSAJE_CHARS)
    historial: list[dict] = Field(default_factory=list)
    idioma: str = Field(default="es", max_length=5)


def _contexto_rapido() -> str:
    """Pequeño resumen en vivo (mes actual) para anclar las respuestas del bot a datos reales."""
    sesion = obtener_sesion()
    try:
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)

        restaurante = sesion.query(Restaurante).filter(Restaurante.estado == True).first()
        nombre_restaurante = restaurante.nombre_comercial if restaurante else "el restaurante"

        total_desperdicio = float(sesion.query(func.coalesce(func.sum(Desperdicio.costo_estimado), 0)).filter(
            Desperdicio.fecha >= inicio_mes
        ).scalar() or 0)

        total_ventas = float(sesion.query(func.coalesce(func.sum(Venta.total), 0)).filter(
            Venta.fecha >= inicio_mes
        ).scalar() or 0)

        num_platos = int(sesion.query(func.count(Plato.id_plato)).filter(Plato.estado == True).scalar() or 0)

        return (
            f"Contexto actual del negocio ({nombre_restaurante}, mes en curso desde {inicio_mes.isoformat()}): "
            f"ventas acumuladas S/ {total_ventas:.2f}; costo estimado de desperdicio S/ {total_desperdicio:.2f}; "
            f"{num_platos} platos activos en el menú. Usa estos datos solo si son relevantes a la pregunta."
        )
    except Exception:
        logger.exception("No se pudo construir el contexto rápido del chatbot")
        return ""
    finally:
        sesion.close()


def _construir_contenidos(historial: list[dict], mensaje: str) -> list[types.Content]:
    """Convierte el historial (rol 'user'/'assistant') al formato de Gemini (rol 'user'/'model')."""
    contenidos = []
    for turno in historial:
        rol_gemini = "model" if turno["role"] == "assistant" else "user"
        contenidos.append(types.Content(role=rol_gemini, parts=[types.Part(text=turno["content"])]))
    contenidos.append(types.Content(role="user", parts=[types.Part(text=mensaje)]))
    return contenidos


@router.post("/mensaje")
def enviar_mensaje(datos: MensajeChatEntrada, current_user: dict = Depends(obtener_usuario_actual)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="El chatbot no está configurado (falta GEMINI_API_KEY).")

    mensaje = datos.mensaje.strip()
    if not mensaje:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    historial_validado = []
    for turno in datos.historial[-MAX_TURNOS_HISTORIAL:]:
        rol = turno.get("rol")
        contenido = turno.get("contenido")
        if rol in ("user", "assistant") and isinstance(contenido, str) and contenido.strip():
            historial_validado.append({"role": rol, "content": contenido.strip()[:MAX_MENSAJE_CHARS]})

    idioma = _idioma_valido(datos.idioma)

    contexto = _contexto_rapido()
    system = (
        SYSTEM_PROMPT_BASE
        + "\n\n" + INSTRUCCION_IDIOMA[idioma]
        + ("\n\n" + contexto if contexto else "")
    )

    contenidos = _construir_contenidos(historial_validado, mensaje)

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        respuesta = client.models.generate_content(
            model=CHATBOT_MODEL,
            contents=contenidos,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=CHATBOT_MAX_TOKENS,
            ),
        )
    except genai_errors.APIError as exc:
        codigo = getattr(exc, "code", None)
        logger.error("Error del API de Gemini (code=%s): %s", codigo, exc)
        if codigo in (401, 403):
            raise HTTPException(status_code=503, detail="El chatbot no está disponible (clave de API de Gemini inválida).")
        if codigo == 429:
            raise HTTPException(status_code=429, detail="El chatbot está saturado. Intenta nuevamente en unos segundos.")
        if codigo and codigo >= 500:
            raise HTTPException(status_code=502, detail="El servicio del chatbot no está disponible en este momento.")
        raise HTTPException(status_code=400, detail="El chatbot no pudo procesar la solicitud (parámetros inválidos).")
    except Exception:
        logger.exception("Error inesperado al llamar al chatbot")
        raise HTTPException(status_code=502, detail="No se pudo conectar con el servicio del chatbot.")

    candidatos = respuesta.candidates or []
    finish_reason = str(candidatos[0].finish_reason) if candidatos else ""
    finish_reason = finish_reason.split(".")[-1]  # tolera tanto 'STOP' como 'FinishReason.STOP'

    if candidatos and finish_reason not in FINISH_REASONS_OK:
        texto = MENSAJE_RECHAZO[idioma]
    else:
        texto = (respuesta.text or "").strip()
        if not texto:
            texto = MENSAJE_RESPUESTA_VACIA[idioma]

    return {"respuesta": texto}
