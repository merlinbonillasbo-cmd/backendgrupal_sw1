from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import get_db
from app.core.security import verify_token
from app.schemas.proyecto import ProyectoCreate, ProyectoUpdate, ProyectoOut
from app.services.proyecto_service import (
    crear_proyecto,
    listar_proyectos_usuario,
    obtener_proyecto_por_id,
    actualizar_proyecto,
    eliminar_proyecto
)
from app.services.pago_service import verificar_limite_proyectos


proyecto_router = APIRouter(
    prefix="/api/proyectos",
    tags=["Proyectos"]
)


@proyecto_router.post("/", response_model=ProyectoOut)
def crear(
    data: ProyectoCreate,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        verificar_limite_proyectos(db, usuario_id)
        return crear_proyecto(db, data, usuario_id)

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


@proyecto_router.get("/", response_model=list[ProyectoOut])
def listar(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_proyectos_usuario(db, usuario_id)

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


@proyecto_router.get("/{proyecto_id}", response_model=ProyectoOut)
def obtener(
    proyecto_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        proyecto = obtener_proyecto_por_id(db, proyecto_id, usuario_id)

        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        return proyecto

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


@proyecto_router.put("/{proyecto_id}", response_model=ProyectoOut)
def editar(
    proyecto_id: int,
    data: ProyectoUpdate,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        proyecto = obtener_proyecto_por_id(db, proyecto_id, usuario_id)

        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        return actualizar_proyecto(db, proyecto, data)

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


@proyecto_router.delete("/{proyecto_id}")
def eliminar(
    proyecto_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        proyecto = obtener_proyecto_por_id(db, proyecto_id, usuario_id)

        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        eliminar_proyecto(db, proyecto)

        return {"mensaje": "Proyecto eliminado correctamente"}

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