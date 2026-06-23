import os
import requests
from sqlalchemy import text as sql_text

from fastapi import HTTPException
from sqlalchemy.orm import Session
from google import genai

from app.core.config import settings
from app.models.audio import Audio
from app.models.proyecto import Proyecto
from app.models.transcripcion import Transcripcion


MODELO_TRANSCRIPCION = "gemini-2.5-flash"


def obtener_audio_del_usuario(
    db: Session,
    audio_id: int,
    usuario_id: int
) -> Audio:
    audio = (
        db.query(Audio)
        .join(Proyecto, Audio.id_proyecto == Proyecto.id)
        .filter(
            Audio.id == audio_id,
            Proyecto.id_usuario == usuario_id
        )
        .first()
    )

    if not audio:
        raise HTTPException(
            status_code=404,
            detail="Audio no encontrado"
        )

    return audio


def contar_palabras(texto: str) -> int:
    if not texto:
        return 0

    return len(texto.split())


def transcribir_audio_con_gemini(ruta_audio: str) -> str:
    if not os.path.exists(ruta_audio):
        raise HTTPException(
            status_code=404,
            detail="Archivo de audio no encontrado en el servidor"
        )

    client = genai.Client(api_key=settings.gemini_api_key)

    archivo = client.files.upload(file=ruta_audio)

    prompt = """
Transcribe el audio completo en español.

Reglas:
- Devuelve únicamente la transcripción.
- No agregues explicación.
- No inventes contenido.
- Mantén el orden original.
- Si hay partes poco claras, marca [inaudible].
"""

    response = client.models.generate_content(
        model=MODELO_TRANSCRIPCION,
        contents=[archivo, prompt]
    )

    texto = response.text

    if not texto or not texto.strip():
        raise HTTPException(
            status_code=500,
            detail="No se pudo generar la transcripción"
        )

    return texto.strip()


def crear_o_reemplazar_transcripcion(
    db: Session,
    audio: Audio,
    texto: str
) -> Transcripcion:
    transcripcion_existente = (
        db.query(Transcripcion)
        .filter(Transcripcion.id_audio == audio.id)
        .first()
    )

    cantidad = contar_palabras(texto)

    if transcripcion_existente:
        transcripcion_existente.texto_generado = texto
        transcripcion_existente.modelo_usado = MODELO_TRANSCRIPCION
        transcripcion_existente.cantidad_palabras = cantidad

        db.commit()
        db.refresh(transcripcion_existente)

        return transcripcion_existente

    nueva_transcripcion = Transcripcion(
        id_audio=audio.id,
        modelo_usado=MODELO_TRANSCRIPCION,
        cantidad_palabras=cantidad,
        texto_generado=texto
    )

    db.add(nueva_transcripcion)
    db.commit()
    db.refresh(nueva_transcripcion)

    return nueva_transcripcion


def obtener_embedding_ollama(texto: str) -> list[float]:
    url = "http://ollama:11434/api/embeddings"
    payload = {
        "model": "nomic-embed-text",
        "prompt": texto
    }
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["embedding"]


def chunk_texto(texto: str, max_caracteres: int = 600) -> list[str]:
    # Separamos el texto por párrafos
    paragraphs = [p.strip() for p in texto.split("\n") if p.strip()]
    chunks = []
    current_chunk = []
    current_len = 0
    for p in paragraphs:
        if len(p) > max_caracteres:
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            chunks.append(p)
        elif current_len + len(p) > max_caracteres:
            chunks.append("\n".join(current_chunk))
            current_chunk = [p]
            current_len = len(p)
        else:
            current_chunk.append(p)
            current_len += len(p) + 1
            
    if current_chunk:
        chunks.append("\n".join(current_chunk))
        
    return chunks


def guardar_fragmentos_transcripcion(db: Session, transcripcion_id: int, chunks: list[str]):
    db.execute(
        sql_text("DELETE FROM fragmento_transcripcion WHERE id_transcripcion = :t_id"),
        {"t_id": transcripcion_id}
    )
    db.commit()

    for idx, chunk in enumerate(chunks):
        try:
            vector_embed = obtener_embedding_ollama(chunk)
            vector_str = f"[{','.join(map(str, vector_embed))}]"
            
            db.execute(
                sql_text("""
                    INSERT INTO fragmento_transcripcion (id_transcripcion, indice_fragmento, texto_fragmento, embedding)
                    VALUES (:t_id, :idx, :texto, CAST(:emb AS vector))
                """),
                {
                    "t_id": transcripcion_id,
                    "idx": idx,
                    "texto": chunk,
                    "emb": vector_str
                }
            )
        except Exception as e:
            print(f"Error al generar embedding para chunk {idx}: {str(e)}")
            continue
    db.commit()


def transcribir_audio(
    db: Session,
    audio_id: int,
    usuario_id: int
) -> Transcripcion:
    audio = obtener_audio_del_usuario(db, audio_id, usuario_id)

    try:
        audio.estado_procesamiento = "PROCESANDO"
        audio.mensaje_error = None
        db.commit()
        db.refresh(audio)

        texto = transcribir_audio_con_gemini(audio.url_audio)

        transcripcion = crear_o_reemplazar_transcripcion(db, audio, texto)

        try:
            chunks = chunk_texto(texto)
            guardar_fragmentos_transcripcion(db, transcripcion.id, chunks)
        except Exception as embed_err:
            print(f"Advertencia: no se pudo guardar fragmentos vectorizados: {str(embed_err)}")

        audio.estado_procesamiento = "COMPLETADO"
        audio.mensaje_error = None
        db.commit()

        return transcripcion

    except HTTPException as e:
        audio.estado_procesamiento = "ERROR"
        audio.mensaje_error = e.detail
        db.commit()
        raise

    except Exception as e:
        audio.estado_procesamiento = "ERROR"
        audio.mensaje_error = str(e)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Error al transcribir el audio: {str(e)}"
        )



def obtener_transcripcion_audio(
    db: Session,
    audio_id: int,
    usuario_id: int
) -> Transcripcion:
    audio = obtener_audio_del_usuario(db, audio_id, usuario_id)

    transcripcion = (
        db.query(Transcripcion)
        .filter(Transcripcion.id_audio == audio.id)
        .first()
    )

    if not transcripcion:
        raise HTTPException(
            status_code=404,
            detail="Este audio todavía no tiene transcripción"
        )

    return transcripcion