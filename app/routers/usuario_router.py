from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import get_db
from app.schemas.usuario import UsuarioOut, UsuarioUpdate
from app.core.security import verify_token
from app.services.usuario_service import obtener_usuario_por_id, actualizar_usuario


usuario_router = APIRouter(
    prefix="/api/usuario",
    tags=["Usuario"]
)


@usuario_router.get("/perfil", response_model=UsuarioOut)
def obtener_perfil(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        usuario = obtener_usuario_por_id(db, usuario_id)

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return usuario

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


@usuario_router.put("/perfil", response_model=UsuarioOut)
def editar_perfil(
    data: UsuarioUpdate,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        usuario = obtener_usuario_por_id(db, usuario_id)

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        usuario_actualizado = actualizar_usuario(db, usuario, data)

        return usuario_actualizado

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