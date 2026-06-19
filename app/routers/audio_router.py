from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import os
import uuid
import shutil

from app.core.db import get_db
from app.models.audio import Audio
from app.models.proyecto import Proyecto
from app.schemas.audio import AudioOut
from app.core.security import verify_token

audio_router = APIRouter()
UPLOAD_DIR = "uploads"

# 1. SUBIR AUDIO A UN PROYECTO (Requiere Token)
@audio_router.post("/proyecto/{proyecto_id}/audio/", response_model=AudioOut)
def subir_audio(
    proyecto_id: int,
    titulo: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario_id: int = Depends(verify_token)
):
    try:
        # Verificar que el proyecto existe y pertenece al usuario
        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.id_usuario == usuario_id).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Carpeta no encontrada o no autorizada")

        # Asegurar que el directorio de subidas existe
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Generar nombre único para el archivo
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ".mp3"
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Guardar archivo físicamente
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Guardar en base de datos
        # Construir la URL del archivo
        url_audio = f"http://127.0.0.1:8000/uploads/{unique_filename}"
        
        nuevo_audio = Audio(
            id_proyecto=proyecto_id,
            titulo=titulo,
            url_audio=url_audio,
            estado_procesamiento="PENDIENTE"
        )
        
        db.add(nuevo_audio)
        db.commit()
        db.refresh(nuevo_audio)
        return nuevo_audio

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir el archivo: {str(e)}")

# 2. LISTAR AUDIOS DE UN PROYECTO (Requiere Token)
@audio_router.get("/proyecto/{proyecto_id}/audio/", response_model=list[AudioOut])
def listar_audios(
    proyecto_id: int,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(verify_token)
):
    try:
        # Verificar propiedad del proyecto
        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.id_usuario == usuario_id).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Carpeta no encontrada o no autorizada")

        audios = db.query(Audio).filter(Audio.id_proyecto == proyecto_id).order_by(Audio.creado_en.desc()).all()
        return audios
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar audios: {str(e)}")

# 3. ELIMINAR AUDIO (Requiere Token)
@audio_router.delete("/audio/{audio_id}")
def eliminar_audio(
    audio_id: int,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(verify_token)
):
    try:
        # Buscar el audio e incluir su relacion de proyecto para validar el id_usuario
        audio = db.query(Audio).join(Proyecto).filter(Audio.id == audio_id, Proyecto.id_usuario == usuario_id).first()
        if not audio:
            raise HTTPException(status_code=404, detail="Audio no encontrado o no autorizado")

        # Eliminar archivo físico
        filename = audio.url_audio.split("/")[-1]
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Advertencia: No se pudo borrar el archivo físico {file_path}: {e}")

        # Eliminar de la base de datos
        db.delete(audio)
        db.commit()
        return {"mensaje": "Audio eliminado exitosamente"}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar audio: {str(e)}")
