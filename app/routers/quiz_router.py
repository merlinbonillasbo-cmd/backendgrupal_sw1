from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database.connection import get_db
from app.core.security import verify_token
from app.services.quiz_service import (
    listar_audios_disponibles,
    crear_quiz_estudio,
    obtener_quiz_usuario,
    guardar_resultado_quiz,
    listar_historial_quizzes
)

quiz_router = APIRouter(
    prefix="/api/quizzes",
    tags=["Quizzes de Estudio"]
)

class QuizCreate(BaseModel):
    titulo: Optional[str] = None
    audio_ids: List[int]

class QuizSubmit(BaseModel):
    bien: int
    mal: int
    respuestas_usuario: List[str]


@quiz_router.get("/audios")
def get_audios_disponibles(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_audios_disponibles(db=db, usuario_id=usuario_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@quiz_router.post("")
def crear_quiz(
    data: QuizCreate,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return crear_quiz_estudio(
            db=db,
            usuario_id=usuario_id,
            titulo=data.titulo,
            audio_ids=data.audio_ids
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@quiz_router.get("/historial/lista")
def get_historial_quizzes(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_historial_quizzes(db=db, usuario_id=usuario_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@quiz_router.get("/{quiz_id}")
def obtener_quiz(
    quiz_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return obtener_quiz_usuario(db=db, quiz_id=quiz_id, usuario_id=usuario_id)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@quiz_router.post("/{quiz_id}/responder")
def responder_quiz(
    quiz_id: int,
    data: QuizSubmit,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return guardar_resultado_quiz(
            db=db,
            quiz_id=quiz_id,
            usuario_id=usuario_id,
            bien=data.bien,
            mal=data.mal,
            respuestas_usuario=data.respuestas_usuario
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
