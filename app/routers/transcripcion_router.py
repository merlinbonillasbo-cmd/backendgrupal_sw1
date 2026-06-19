from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import get_db
from app.core.security import verify_token
from app.schemas.transcripcion import TranscripcionOut
from app.services.transcripcion_service import (
    transcribir_audio,
    obtener_transcripcion_audio
)


transcripcion_router = APIRouter(
    prefix="/api/transcripciones",
    tags=["Transcripciones"]
)


@transcripcion_router.post("/audio/{audio_id}", response_model=TranscripcionOut)
def generar_transcripcion(
    audio_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return transcribir_audio(db, audio_id, usuario_id)

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


@transcripcion_router.get("/audio/{audio_id}", response_model=TranscripcionOut)
def ver_transcripcion(
    audio_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return obtener_transcripcion_audio(db, audio_id, usuario_id)

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