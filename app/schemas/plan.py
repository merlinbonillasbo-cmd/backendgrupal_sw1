from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    precio: Decimal = Field(default=Decimal("0.00"), ge=0)
    max_audios: Optional[int] = Field(None, ge=0)
    max_proyectos: Optional[int] = Field(None, ge=0)
    max_transcripciones: Optional[int] = Field(None, ge=0)
    max_resumenes: Optional[int] = Field(None, ge=0)


class PlanUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = None
    precio: Optional[Decimal] = Field(None, ge=0)
    max_audios: Optional[int] = Field(None, ge=0)
    max_proyectos: Optional[int] = Field(None, ge=0)
    max_transcripciones: Optional[int] = Field(None, ge=0)
    max_resumenes: Optional[int] = Field(None, ge=0)
    activo: Optional[bool] = None


class PlanOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    precio: Decimal
    max_audios: Optional[int] = None
    max_proyectos: Optional[int] = None
    max_transcripciones: Optional[int] = None
    max_resumenes: Optional[int] = None
    activo: bool
    creado_en: datetime

    class Config:
        from_attributes = True


class SuscripcionOut(BaseModel):
    id: int
    id_usuario: int
    id_plan: int
    estado: str
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    creado_en: datetime
    plan: Optional[PlanOut] = None

    class Config:
        from_attributes = True


class SuscripcionCambiarPlan(BaseModel):
    id_plan: int


# ── Pago ──────────────────────────────────────────────────────────────────────

class PagoRequest(BaseModel):
    """Datos que envía el frontend para procesar el pago simulado."""
    id_plan: int
    numero_tarjeta: str = Field(..., min_length=13, max_length=19)
    nombre_titular: str = Field(..., min_length=2, max_length=100)
    mes_expiracion: str = Field(..., pattern=r"^(0[1-9]|1[0-2])$")
    anio_expiracion: str = Field(..., pattern=r"^\d{2}$")
    cvv: str = Field(..., min_length=3, max_length=4)


class PagoOut(BaseModel):
    id: int
    referencia: str
    monto: Decimal
    moneda: str
    ultimos_digitos: Optional[str] = None
    tipo_tarjeta: Optional[str] = None
    estado: str
    mensaje_respuesta: Optional[str] = None
    creado_en: datetime
    plan: Optional[PlanOut] = None
    suscripcion: Optional[SuscripcionOut] = None

    class Config:
        from_attributes = True
