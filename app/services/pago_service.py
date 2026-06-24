"""
pago_service.py
Lógica de pago simulado y control de límites por plan.

El simulador evalúa la tarjeta con estas reglas deterministas:
- Número terminado en 0000     → RECHAZADO (fondos insuficientes)
- Número terminado en 1111     → RECHAZADO (tarjeta bloqueada)
- Número terminado en 9999     → RECHAZADO (tarjeta expirada)
- CVV "000"                    → RECHAZADO (CVV inválido)
- Todo lo demás                → APROBADO

Si el plan es gratuito (precio == 0) se aprueba sin validar datos de tarjeta.
"""

import uuid
import re
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.pago import Pago
from app.models.plan import Plan
from app.models.suscripcion import Suscripcion
from app.models.audio import Audio
from app.models.proyecto import Proyecto
from app.models.resumen import Resumen
from app.models.transcripcion import Transcripcion
from app.schemas.plan import PagoRequest


# ─── Detección de tipo de tarjeta ────────────────────────────────────────────

def detectar_tipo_tarjeta(numero: str) -> str:
    limpio = re.sub(r"\D", "", numero)
    if limpio.startswith("4"):
        return "VISA"
    if limpio[:2] in ("51", "52", "53", "54", "55") or (51 <= int(limpio[:4]) <= 5500):
        return "MASTERCARD"
    if limpio[:2] in ("34", "37"):
        return "AMEX"
    if limpio.startswith("6011") or limpio.startswith("65"):
        return "DISCOVER"
    return "OTRA"


def obtener_ultimos_digitos(numero: str) -> str:
    limpio = re.sub(r"\D", "", numero)
    return limpio[-4:] if len(limpio) >= 4 else limpio


# ─── Motor de simulación ─────────────────────────────────────────────────────

def _simular_procesamiento(numero: str, cvv: str, mes: str, anio: str) -> tuple[bool, str]:
    """
    Retorna (aprobado: bool, mensaje: str).
    Aplica reglas deterministas sobre el número y CVV.
    """
    limpio = re.sub(r"\D", "", numero)

    # Validación básica de longitud (Luhn no implementado a propósito, es simulación)
    if len(limpio) < 13 or len(limpio) > 19:
        return False, "Número de tarjeta inválido"

    if cvv == "000":
        return False, "CVV inválido. Verifica el código de seguridad de tu tarjeta."

    if limpio.endswith("0000"):
        return False, "Transacción rechazada: fondos insuficientes."

    if limpio.endswith("1111"):
        return False, "Transacción rechazada: tarjeta bloqueada o reportada."

    if limpio.endswith("9999"):
        return False, "Transacción rechazada: tarjeta expirada o cancelada por el banco."

    # Validación de fecha de expiración
    anio_completo = 2000 + int(anio)
    ahora = datetime.now()
    if anio_completo < ahora.year or (anio_completo == ahora.year and int(mes) < ahora.month):
        return False, "La tarjeta está vencida. Usa una con fecha de expiración vigente."

    return True, "Transacción aprobada exitosamente."


# ─── Función principal ───────────────────────────────────────────────────────

def procesar_pago_suscripcion(
    db: Session,
    usuario_id: int,
    data: PagoRequest
) -> dict:
    """
    1. Obtiene el plan.
    2. Registra el intento de pago.
    3. Simula la pasarela de pago.
    4. Si aprobado → activa suscripción.
    5. Devuelve resultado completo.
    """
    plan = db.query(Plan).filter(Plan.id == data.id_plan).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    if not plan.activo:
        raise HTTPException(status_code=400, detail="El plan seleccionado no está disponible")

    # Si el plan actual ya es el mismo, no reprocesar
    sub_actual = (
        db.query(Suscripcion)
        .filter(Suscripcion.id_usuario == usuario_id, Suscripcion.estado == "ACTIVA")
        .first()
    )
    if sub_actual and sub_actual.id_plan == data.id_plan:
        raise HTTPException(status_code=400, detail="Ya estás suscrito a este plan.")

    referencia = str(uuid.uuid4()).replace("-", "")[:32].upper()
    ultimos = obtener_ultimos_digitos(data.numero_tarjeta)
    tipo = detectar_tipo_tarjeta(data.numero_tarjeta)
    monto = plan.precio

    # Registrar intento de pago en estado PENDIENTE
    pago = Pago(
        id_usuario=usuario_id,
        id_plan=plan.id,
        referencia=referencia,
        monto=monto,
        ultimos_digitos=ultimos,
        tipo_tarjeta=tipo,
        estado="PENDIENTE",
        mensaje_respuesta="Procesando..."
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)

    # Planes gratuitos no requieren datos de tarjeta reales → aprobación directa
    if monto == Decimal("0.00") or monto == 0:
        aprobado = True
        mensaje = "Plan gratuito activado sin cargo."
    else:
        aprobado, mensaje = _simular_procesamiento(
            data.numero_tarjeta,
            data.cvv,
            data.mes_expiracion,
            data.anio_expiracion
        )

    # Actualizar estado del pago
    pago.estado = "APROBADO" if aprobado else "RECHAZADO"
    pago.mensaje_respuesta = mensaje
    db.commit()
    db.refresh(pago)

    nueva_sub = None
    if aprobado:
        # Cancelar suscripción anterior
        if sub_actual:
            sub_actual.estado = "CANCELADA"
            sub_actual.fecha_fin = datetime.now(timezone.utc)

        # Crear nueva suscripción activa
        nueva_sub = Suscripcion(
            id_usuario=usuario_id,
            id_plan=plan.id,
            estado="ACTIVA"
        )
        db.add(nueva_sub)
        db.commit()
        db.refresh(nueva_sub)
        nueva_sub.plan  # eager load

    return {
        "pago": {
            "id": pago.id,
            "referencia": pago.referencia,
            "monto": float(pago.monto),
            "moneda": pago.moneda,
            "ultimos_digitos": pago.ultimos_digitos,
            "tipo_tarjeta": pago.tipo_tarjeta,
            "estado": pago.estado,
            "mensaje_respuesta": pago.mensaje_respuesta,
            "creado_en": pago.creado_en.isoformat(),
        },
        "aprobado": aprobado,
        "plan": {
            "id": plan.id,
            "nombre": plan.nombre,
            "descripcion": plan.descripcion,
            "precio": float(plan.precio),
            "max_audios": plan.max_audios,
            "max_proyectos": plan.max_proyectos,
            "max_transcripciones": plan.max_transcripciones,
            "max_resumenes": plan.max_resumenes,
        },
        "suscripcion": {
            "id": nueva_sub.id,
            "id_plan": nueva_sub.id_plan,
            "estado": nueva_sub.estado,
            "fecha_inicio": nueva_sub.fecha_inicio.isoformat(),
        } if nueva_sub else None,
    }


# ─── Historial de pagos del usuario ──────────────────────────────────────────

def historial_pagos_usuario(db: Session, usuario_id: int) -> list[Pago]:
    return (
        db.query(Pago)
        .filter(Pago.id_usuario == usuario_id)
        .order_by(Pago.creado_en.desc())
        .all()
    )


# ─── Control de límites por plan ─────────────────────────────────────────────

def verificar_limite_audios(db: Session, usuario_id: int):
    """
    Lanza 403 si el usuario alcanzó el límite de audios de su plan activo.
    Llamar antes de crear un audio.
    """
    sub = (
        db.query(Suscripcion)
        .filter(Suscripcion.id_usuario == usuario_id, Suscripcion.estado == "ACTIVA")
        .first()
    )
    if not sub:
        return  # Sin suscripción → sin restricción (acceso básico)

    plan = db.query(Plan).filter(Plan.id == sub.id_plan).first()
    if not plan or plan.max_audios is None:
        return  # Ilimitado

    total_audios = (
        db.query(Audio)
        .join(Proyecto, Audio.id_proyecto == Proyecto.id)
        .filter(Proyecto.id_usuario == usuario_id)
        .count()
    )
    if total_audios >= plan.max_audios:
        raise HTTPException(
            status_code=403,
            detail=f"Has alcanzado el límite de {plan.max_audios} audios del plan '{plan.nombre}'. Mejora tu suscripción para continuar."
        )


def verificar_limite_proyectos(db: Session, usuario_id: int):
    sub = (
        db.query(Suscripcion)
        .filter(Suscripcion.id_usuario == usuario_id, Suscripcion.estado == "ACTIVA")
        .first()
    )
    if not sub:
        return

    plan = db.query(Plan).filter(Plan.id == sub.id_plan).first()
    if not plan or plan.max_proyectos is None:
        return

    total = db.query(Proyecto).filter(Proyecto.id_usuario == usuario_id).count()
    if total >= plan.max_proyectos:
        raise HTTPException(
            status_code=403,
            detail=f"Has alcanzado el límite de {plan.max_proyectos} proyectos del plan '{plan.nombre}'. Mejora tu suscripción para continuar."
        )


def verificar_limite_transcripciones(db: Session, usuario_id: int):
    sub = (
        db.query(Suscripcion)
        .filter(Suscripcion.id_usuario == usuario_id, Suscripcion.estado == "ACTIVA")
        .first()
    )
    if not sub:
        return

    plan = db.query(Plan).filter(Plan.id == sub.id_plan).first()
    if not plan or plan.max_transcripciones is None:
        return

    total = (
        db.query(Transcripcion)
        .join(Audio, Transcripcion.id_audio == Audio.id)
        .join(Proyecto, Audio.id_proyecto == Proyecto.id)
        .filter(Proyecto.id_usuario == usuario_id)
        .count()
    )
    if total >= plan.max_transcripciones:
        raise HTTPException(
            status_code=403,
            detail=f"Has alcanzado el límite de {plan.max_transcripciones} transcripciones del plan '{plan.nombre}'. Mejora tu suscripción para continuar."
        )


def verificar_limite_resumenes(db: Session, usuario_id: int):
    sub = (
        db.query(Suscripcion)
        .filter(Suscripcion.id_usuario == usuario_id, Suscripcion.estado == "ACTIVA")
        .first()
    )
    if not sub:
        return

    plan = db.query(Plan).filter(Plan.id == sub.id_plan).first()
    if not plan or plan.max_resumenes is None:
        return

    from app.models.solicitud import Solicitud
    total = (
        db.query(Resumen)
        .join(Solicitud, Resumen.id_solicitud == Solicitud.id)
        .filter(Solicitud.id_usuario == usuario_id)
        .count()
    )
    if total >= plan.max_resumenes:
        raise HTTPException(
            status_code=403,
            detail=f"Has alcanzado el límite de {plan.max_resumenes} resúmenes del plan '{plan.nombre}'. Mejora tu suscripción para continuar."
        )
