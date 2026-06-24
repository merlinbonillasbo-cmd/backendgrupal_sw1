from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.database.connection import get_db
from app.schemas.plan import PlanOut, SuscripcionOut, SuscripcionCambiarPlan, PagoRequest
from app.services.plan_service import (
    asegurar_suscripcion_gratuita,
    cambiar_plan_usuario,
    cancelar_suscripcion,
    historial_suscripciones_usuario,
    listar_planes,
    obtener_suscripcion_activa,
)
from app.services.pago_service import (
    procesar_pago_suscripcion,
    historial_pagos_usuario,
)


suscripcion_router = APIRouter(
    prefix="/api/suscripciones",
    tags=["Suscripciones"]
)


@suscripcion_router.get("/planes", response_model=list[PlanOut])
def get_planes_disponibles(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Devuelve todos los planes activos para que el usuario pueda elegir."""
    try:
        return listar_planes(db, solo_activos=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@suscripcion_router.get("/mi-suscripcion", response_model=SuscripcionOut)
def get_mi_suscripcion(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Devuelve la suscripción activa del usuario. Si no tiene, asigna el plan gratuito."""
    try:
        sub = obtener_suscripcion_activa(db, usuario_id)
        if not sub:
            sub = asegurar_suscripcion_gratuita(db, usuario_id)
        if not sub:
            raise HTTPException(status_code=404, detail="No se encontró suscripción activa ni plan gratuito disponible")
        return sub
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@suscripcion_router.post("/cambiar-plan", response_model=SuscripcionOut)
def cambiar_plan(
    data: SuscripcionCambiarPlan,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Cambia el plan activo del usuario al plan indicado."""
    try:
        return cambiar_plan_usuario(db, usuario_id, data.id_plan)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@suscripcion_router.post("/cancelar", response_model=SuscripcionOut)
def cancelar_mi_suscripcion(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Cancela la suscripción activa del usuario."""
    try:
        return cancelar_suscripcion(db, usuario_id)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@suscripcion_router.get("/historial", response_model=list[SuscripcionOut])
def get_historial(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Historial completo de suscripciones del usuario."""
    try:
        return historial_suscripciones_usuario(db, usuario_id)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@suscripcion_router.post("/pagar")
def pagar_suscripcion(
    data: PagoRequest,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Procesa el pago simulado para suscribirse a un plan.
    Valida los datos de tarjeta, registra la transacción y,
    si es aprobada, activa la suscripción al plan seleccionado.
    """
    try:
        return procesar_pago_suscripcion(db, usuario_id, data)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@suscripcion_router.get("/pagos")
def get_historial_pagos(
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Historial de todas las transacciones de pago del usuario."""
    try:
        pagos = historial_pagos_usuario(db, usuario_id)
        return [
            {
                "id": p.id,
                "referencia": p.referencia,
                "monto": float(p.monto),
                "moneda": p.moneda,
                "ultimos_digitos": p.ultimos_digitos,
                "tipo_tarjeta": p.tipo_tarjeta,
                "estado": p.estado,
                "mensaje_respuesta": p.mensaje_respuesta,
                "creado_en": p.creado_en.isoformat(),
                "plan": {
                    "id": p.plan.id,
                    "nombre": p.plan.nombre,
                    "precio": float(p.plan.precio),
                } if p.plan else None,
            }
            for p in pagos
        ]
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
