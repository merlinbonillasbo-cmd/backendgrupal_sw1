from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.database.connection import get_db
from app.core.security import verify_token
from app.services.presentacion_service import (
    listar_audios_disponibles,
    crear_presentacion_estudio,
    obtener_presentacion_usuario,
    guardar_cambios_presentacion,
    listar_historial_presentaciones
)

presentacion_router = APIRouter(
    prefix="/api/presentaciones",
    tags=["Presentaciones de Estudio"]
)


class PresentacionCreate(BaseModel):
    titulo: Optional[str] = None
    audio_ids: List[int]


class PresentacionSave(BaseModel):
    titulo: str
    contenido: List[Dict[str, Any]]
    diseno: Dict[str, Any]


@presentacion_router.get("/audios")
def get_audios_disponibles(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_audios_disponibles(db=db, usuario_id=usuario_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@presentacion_router.post("")
def crear_presentacion(
    data: PresentacionCreate,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return crear_presentacion_estudio(
            db=db,
            usuario_id=usuario_id,
            titulo=data.titulo,
            audio_ids=data.audio_ids
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@presentacion_router.get("/historial/lista")
def get_historial_presentaciones(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_historial_presentaciones(db=db, usuario_id=usuario_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@presentacion_router.get("/{pres_id}")
def obtener_presentacion(
    pres_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return obtener_presentacion_usuario(db=db, pres_id=pres_id, usuario_id=usuario_id)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@presentacion_router.put("/{pres_id}/guardar")
def guardar_presentacion(
    pres_id: int,
    data: PresentacionSave,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return guardar_cambios_presentacion(
            db=db,
            pres_id=pres_id,
            usuario_id=usuario_id,
            titulo=data.titulo,
            contenido=data.contenido,
            diseno=data.diseno
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
