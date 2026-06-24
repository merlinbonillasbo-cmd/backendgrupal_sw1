from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import get_db
from app.core.security import verify_token
from app.schemas.audio import AudioOut
from app.services.audio_service import (
    crear_audio,
    listar_audios_por_proyecto,
    obtener_audio_por_id,
    eliminar_audio
)
from app.services.pago_service import verificar_limite_audios


audio_router = APIRouter(
    prefix="/api/audios",
    tags=["Audios"]
)


@audio_router.post("/proyecto/{proyecto_id}", response_model=AudioOut)
def subir_audio(
    proyecto_id: int,
    titulo: str = Form(...),
    file: UploadFile = File(...),
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        # Verificar límite de audios del plan activo
        verificar_limite_audios(db, usuario_id)
        return crear_audio(db, proyecto_id, usuario_id, titulo, file)

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error en la base de datos: {str(e)}"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )


@audio_router.get("/proyecto/{proyecto_id}", response_model=list[AudioOut])
def listar_audios(
    proyecto_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_audios_por_proyecto(db, proyecto_id, usuario_id)

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la base de datos: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )


@audio_router.delete("/{audio_id}")
def borrar_audio(
    audio_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        audio = obtener_audio_por_id(db, audio_id, usuario_id)

        if not audio:
            raise HTTPException(status_code=404, detail="Audio no encontrado")

        eliminar_audio(db, audio)

        return {"mensaje": "Audio eliminado correctamente"}

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error en la base de datos: {str(e)}"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )