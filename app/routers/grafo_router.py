from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import get_db
from app.core.security import verify_token
from app.schemas.grafo import GrafoCreate, GrafoOut
from app.services.grafo_service import (
    generar_grafo_proyecto,
    obtener_ultimo_grafo_proyecto,
    listar_grafos_proyecto,
    obtener_grafo_por_id,
    eliminar_grafo_usuario
)


grafo_router = APIRouter(
    prefix="/api/grafos",
    tags=["Grafos de conocimiento"]
)


@grafo_router.post("/proyecto/{proyecto_id}", response_model=GrafoOut)
def generar_grafo(
    proyecto_id: int,
    data: GrafoCreate,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return generar_grafo_proyecto(
            db=db,
            proyecto_id=proyecto_id,
            usuario_id=usuario_id,
            nivel_detalle=data.nivel_detalle
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


@grafo_router.get("/proyecto/{proyecto_id}/ultimo", response_model=GrafoOut)
def ver_ultimo_grafo(
    proyecto_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return obtener_ultimo_grafo_proyecto(
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


@grafo_router.get("/proyecto/{proyecto_id}/historial", response_model=list[GrafoOut])
def historial_grafos(
    proyecto_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_grafos_proyecto(
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


@grafo_router.get("/{grafo_id}", response_model=GrafoOut)
def ver_grafo(
    grafo_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return obtener_grafo_por_id(
            db=db,
            grafo_id=grafo_id,
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


@grafo_router.delete("/{grafo_id}")
def eliminar_grafo(
    grafo_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        eliminar_grafo_usuario(
            db=db,
            grafo_id=grafo_id,
            usuario_id=usuario_id
        )

        return {"mensaje": "Grafo eliminado correctamente"}

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