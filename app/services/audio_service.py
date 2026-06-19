import os
import shutil
from uuid import uuid4

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.audio import Audio
from app.models.proyecto import Proyecto


UPLOAD_DIR = "uploads/audios"


def verificar_proyecto_usuario(db: Session, proyecto_id: int, usuario_id: int) -> Proyecto:
    proyecto = (
        db.query(Proyecto)
        .filter(
            Proyecto.id == proyecto_id,
            Proyecto.id_usuario == usuario_id
        )
        .first()
    )

    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return proyecto


def guardar_archivo_audio(file: UploadFile) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    extension = os.path.splitext(file.filename or "")[1].lower()

    extensiones_permitidas = [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"]

    if extension not in extensiones_permitidas:
        raise HTTPException(
            status_code=400,
            detail="Formato de audio no permitido"
        )

    nombre_archivo = f"{uuid4()}{extension}"
    ruta_archivo = os.path.join(UPLOAD_DIR, nombre_archivo)

    with open(ruta_archivo, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return ruta_archivo


def crear_audio(
    db: Session,
    proyecto_id: int,
    usuario_id: int,
    titulo: str,
    file: UploadFile
) -> Audio:
    verificar_proyecto_usuario(db, proyecto_id, usuario_id)

    ruta_audio = guardar_archivo_audio(file)

    nuevo_audio = Audio(
        id_proyecto=proyecto_id,
        titulo=titulo,
        url_audio=ruta_audio,
        estado_procesamiento="PENDIENTE"
    )

    db.add(nuevo_audio)
    db.commit()
    db.refresh(nuevo_audio)

    return nuevo_audio


def listar_audios_por_proyecto(db: Session, proyecto_id: int, usuario_id: int):
    verificar_proyecto_usuario(db, proyecto_id, usuario_id)

    return (
        db.query(Audio)
        .filter(Audio.id_proyecto == proyecto_id)
        .order_by(Audio.creado_en.desc())
        .all()
    )


def obtener_audio_por_id(db: Session, audio_id: int, usuario_id: int):
    return (
        db.query(Audio)
        .join(Proyecto, Audio.id_proyecto == Proyecto.id)
        .filter(
            Audio.id == audio_id,
            Proyecto.id_usuario == usuario_id
        )
        .first()
    )


def eliminar_audio(db: Session, audio: Audio) -> None:
    if audio.url_audio and os.path.exists(audio.url_audio):
        os.remove(audio.url_audio)

    db.delete(audio)
    db.commit()