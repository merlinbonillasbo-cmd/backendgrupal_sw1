from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.database.connection import get_db
from app.schemas.plan import PlanCreate, PlanOut, PlanUpdate, SuscripcionOut, SuscripcionCambiarPlan
from app.schemas.usuario import UsuarioOut
from app.services.plan_service import (
    activar_plan,
    cambiar_estado_usuario,
    crear_plan,
    desactivar_plan,
    listar_planes,
    listar_suscripciones,
    listar_usuarios_admin,
    obtener_metricas,
    obtener_plan_por_id,
    actualizar_plan,
)


admin_router = APIRouter(
    prefix="/api/admin",
    tags=["Administración"]
)


# ─── Planes ──────────────────────────────────────────────────────────────────

@admin_router.get("/planes", response_model=list[PlanOut])
def get_todos_los_planes(
    solo_activos: bool = Query(False),
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_planes(db, solo_activos=solo_activos)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@admin_router.post("/planes", response_model=PlanOut)
def crear_nuevo_plan(
    data: PlanCreate,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return crear_plan(db, usuario_id, data)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@admin_router.put("/planes/{plan_id}", response_model=PlanOut)
def editar_plan(
    plan_id: int,
    data: PlanUpdate,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return actualizar_plan(db, usuario_id, plan_id, data)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@admin_router.patch("/planes/{plan_id}/desactivar", response_model=PlanOut)
def deshabilitar_plan(
    plan_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return desactivar_plan(db, usuario_id, plan_id)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@admin_router.patch("/planes/{plan_id}/activar", response_model=PlanOut)
def habilitar_plan(
    plan_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return activar_plan(db, usuario_id, plan_id)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


# ─── Suscripciones ───────────────────────────────────────────────────────────

@admin_router.get("/suscripciones", response_model=list[SuscripcionOut])
def get_suscripciones_activas(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_suscripciones(db, usuario_id)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


# ─── Gestión de Usuarios ─────────────────────────────────────────────────────

@admin_router.get("/usuarios", response_model=list[UsuarioOut])
def get_usuarios(
    busqueda: Optional[str] = Query(None),
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_usuarios_admin(db, usuario_id, busqueda)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@admin_router.patch("/usuarios/{id_usuario}/activar", response_model=UsuarioOut)
def activar_usuario(
    id_usuario: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return cambiar_estado_usuario(db, usuario_id, id_usuario, True)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@admin_router.patch("/usuarios/{id_usuario}/desactivar", response_model=UsuarioOut)
def desactivar_usuario(
    id_usuario: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return cambiar_estado_usuario(db, usuario_id, id_usuario, False)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


# ─── Métricas ────────────────────────────────────────────────────────────────

@admin_router.get("/metricas")
def get_metricas(
    fecha_inicio: Optional[str] = Query(None, description="YYYY-MM-DD"),
    fecha_fin: Optional[str] = Query(None, description="YYYY-MM-DD"),
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return obtener_metricas(db, usuario_id, fecha_inicio, fecha_fin)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
