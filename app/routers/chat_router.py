from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import get_db
from app.core.security import verify_token
from app.schemas.chat import (
    ChatPreguntaCreate,
    ChatRespuestaOut,
    ChatConversacionOut,
    ChatMensajeOut
)
from app.services.chat_service import (
    preguntar_sobre_proyecto,
    listar_conversaciones_proyecto,
    listar_mensajes_conversacion,
    eliminar_conversacion_usuario
)


chat_router = APIRouter(
    prefix="/api/chat",
    tags=["Chat inteligente"]
)


@chat_router.post("/proyecto/{proyecto_id}/preguntar", response_model=ChatRespuestaOut)
def preguntar(
    proyecto_id: int,
    data: ChatPreguntaCreate,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return preguntar_sobre_proyecto(
            db=db,
            proyecto_id=proyecto_id,
            usuario_id=usuario_id,
            pregunta=data.pregunta,
            id_conversacion=data.id_conversacion
        )

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


@chat_router.get("/proyecto/{proyecto_id}/conversaciones", response_model=list[ChatConversacionOut])
def listar_conversaciones(
    proyecto_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_conversaciones_proyecto(
            db=db,
            proyecto_id=proyecto_id,
            usuario_id=usuario_id
        )

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


@chat_router.get("/conversacion/{conversacion_id}/mensajes", response_model=list[ChatMensajeOut])
def listar_mensajes(
    conversacion_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_mensajes_conversacion(
            db=db,
            conversacion_id=conversacion_id,
            usuario_id=usuario_id
        )

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


@chat_router.delete("/conversacion/{conversacion_id}")
def eliminar_conversacion(
    conversacion_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        eliminar_conversacion_usuario(
            db=db,
            conversacion_id=conversacion_id,
            usuario_id=usuario_id
        )

        return {"mensaje": "Conversación eliminada correctamente"}

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