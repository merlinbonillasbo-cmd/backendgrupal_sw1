from fastapi import HTTPException
from sqlalchemy.orm import Session
from google import genai

from app.core.config import settings
from app.models.proyecto import Proyecto
from app.models.audio import Audio
from app.models.transcripcion import Transcripcion
from app.models.chat_conversacion import ChatConversacion
from app.models.chat_mensaje import ChatMensaje


MODELO_CHAT = "gemini-2.5-flash"


def verificar_proyecto_usuario(
    db: Session,
    proyecto_id: int,
    usuario_id: int
) -> Proyecto:
    proyecto = (
        db.query(Proyecto)
        .filter(
            Proyecto.id == proyecto_id,
            Proyecto.id_usuario == usuario_id
        )
        .first()
    )

    if not proyecto:
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado"
        )

    return proyecto


def obtener_transcripciones_del_proyecto(
    db: Session,
    proyecto_id: int,
    usuario_id: int
) -> list[tuple[Audio, Transcripcion]]:
    verificar_proyecto_usuario(db, proyecto_id, usuario_id)

    resultados = (
        db.query(Audio, Transcripcion)
        .join(Transcripcion, Transcripcion.id_audio == Audio.id)
        .filter(Audio.id_proyecto == proyecto_id)
        .order_by(Audio.creado_en.asc())
        .all()
    )

    transcripciones_validas = []

    for audio, transcripcion in resultados:
        if transcripcion.texto_generado and transcripcion.texto_generado.strip():
            transcripciones_validas.append((audio, transcripcion))

    if not transcripciones_validas:
        raise HTTPException(
            status_code=400,
            detail="El proyecto todavía no tiene audios transcritos para consultar"
        )

    return transcripciones_validas


def construir_contexto_proyecto(
    transcripciones: list[tuple[Audio, Transcripcion]]
) -> str:
    partes = []

    for index, (audio, transcripcion) in enumerate(transcripciones, start=1):
        partes.append(
            f"""
[AUDIO {index}]
Título: {audio.titulo}
Fecha de subida: {audio.creado_en}

Transcripción:
{transcripcion.texto_generado}
"""
        )

    return "\n\n---\n\n".join(partes)


def crear_prompt_chat(contexto: str, pregunta: str) -> str:
    return f"""
Eres un asistente inteligente que responde preguntas usando únicamente el contenido de audios transcritos.

Reglas obligatorias:
- Responde solo con base en el contexto proporcionado.
- No inventes información.
- Si la respuesta no aparece en el contexto, di claramente: "No encontré esa información en los audios del proyecto".
- Responde en español.
- Sé claro, ordenado y útil.
- Si hay tareas, decisiones o compromisos, preséntalos en lista.
- Si la pregunta pide explicación, explica de forma sencilla.

Contexto de los audios del proyecto:
{contexto}

Pregunta del usuario:
{pregunta}
"""


def generar_respuesta_con_gemini(contexto: str, pregunta: str) -> str:
    client = genai.Client(api_key=settings.gemini_api_key)

    prompt = crear_prompt_chat(contexto, pregunta)

    response = client.models.generate_content(
        model=MODELO_CHAT,
        contents=prompt
    )

    respuesta = response.text

    if not respuesta or not respuesta.strip():
        raise HTTPException(
            status_code=500,
            detail="No se pudo generar una respuesta"
        )

    return respuesta.strip()


def crear_conversacion(
    db: Session,
    usuario_id: int,
    proyecto_id: int,
    pregunta: str
) -> ChatConversacion:
    titulo = pregunta.strip()

    if len(titulo) > 80:
        titulo = titulo[:80] + "..."

    conversacion = ChatConversacion(
        id_usuario=usuario_id,
        id_proyecto=proyecto_id,
        titulo=titulo
    )

    db.add(conversacion)
    db.commit()
    db.refresh(conversacion)

    return conversacion


def obtener_conversacion_usuario(
    db: Session,
    conversacion_id: int,
    usuario_id: int,
    proyecto_id: int
) -> ChatConversacion:
    conversacion = (
        db.query(ChatConversacion)
        .filter(
            ChatConversacion.id == conversacion_id,
            ChatConversacion.id_usuario == usuario_id,
            ChatConversacion.id_proyecto == proyecto_id
        )
        .first()
    )

    if not conversacion:
        raise HTTPException(
            status_code=404,
            detail="Conversación no encontrada"
        )

    return conversacion


def guardar_mensaje(
    db: Session,
    conversacion_id: int,
    rol: str,
    contenido: str
) -> ChatMensaje:
    mensaje = ChatMensaje(
        id_conversacion=conversacion_id,
        rol=rol,
        contenido=contenido
    )

    db.add(mensaje)
    db.commit()
    db.refresh(mensaje)

    return mensaje


def preguntar_sobre_proyecto(
    db: Session,
    proyecto_id: int,
    usuario_id: int,
    pregunta: str,
    id_conversacion: int | None = None
):
    verificar_proyecto_usuario(db, proyecto_id, usuario_id)

    transcripciones = obtener_transcripciones_del_proyecto(
        db=db,
        proyecto_id=proyecto_id,
        usuario_id=usuario_id
    )

    contexto = construir_contexto_proyecto(transcripciones)

    if id_conversacion:
        conversacion = obtener_conversacion_usuario(
            db=db,
            conversacion_id=id_conversacion,
            usuario_id=usuario_id,
            proyecto_id=proyecto_id
        )
    else:
        conversacion = crear_conversacion(
            db=db,
            usuario_id=usuario_id,
            proyecto_id=proyecto_id,
            pregunta=pregunta
        )

    mensaje_usuario = guardar_mensaje(
        db=db,
        conversacion_id=conversacion.id,
        rol="USUARIO",
        contenido=pregunta
    )

    try:
        respuesta_ia = generar_respuesta_con_gemini(
            contexto=contexto,
            pregunta=pregunta
        )

        mensaje_ia = guardar_mensaje(
            db=db,
            conversacion_id=conversacion.id,
            rol="IA",
            contenido=respuesta_ia
        )

        return {
            "conversacion": conversacion,
            "pregunta": mensaje_usuario,
            "respuesta": mensaje_ia
        }

    except Exception as e:
        mensaje_error = guardar_mensaje(
            db=db,
            conversacion_id=conversacion.id,
            rol="IA",
            contenido=f"Ocurrió un error al generar la respuesta: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Error al generar respuesta del chat: {str(e)}"
        )


def listar_conversaciones_proyecto(
    db: Session,
    proyecto_id: int,
    usuario_id: int
):
    verificar_proyecto_usuario(db, proyecto_id, usuario_id)

    return (
        db.query(ChatConversacion)
        .filter(
            ChatConversacion.id_usuario == usuario_id,
            ChatConversacion.id_proyecto == proyecto_id
        )
        .order_by(ChatConversacion.creado_en.desc())
        .all()
    )


def listar_mensajes_conversacion(
    db: Session,
    conversacion_id: int,
    usuario_id: int
):
    conversacion = (
        db.query(ChatConversacion)
        .filter(
            ChatConversacion.id == conversacion_id,
            ChatConversacion.id_usuario == usuario_id
        )
        .first()
    )

    if not conversacion:
        raise HTTPException(
            status_code=404,
            detail="Conversación no encontrada"
        )

    mensajes = (
        db.query(ChatMensaje)
        .filter(ChatMensaje.id_conversacion == conversacion_id)
        .order_by(ChatMensaje.creado_en.asc())
        .all()
    )

    return mensajes


def eliminar_conversacion_usuario(
    db: Session,
    conversacion_id: int,
    usuario_id: int
):
    conversacion = (
        db.query(ChatConversacion)
        .filter(
            ChatConversacion.id == conversacion_id,
            ChatConversacion.id_usuario == usuario_id
        )
        .first()
    )

    if not conversacion:
        raise HTTPException(
            status_code=404,
            detail="Conversación no encontrada"
        )

    db.delete(conversacion)
    db.commit()