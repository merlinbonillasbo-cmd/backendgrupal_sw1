from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


class ResumenCreate(BaseModel):
    tipo_resumen: str = Field(..., pattern="^(CORTO|MEDIO|DETALLADO)$")


class ResumenOut(BaseModel):
    id: int
    id_solicitud: int
    titulo: Optional[str] = None
    tipo_resumen: str
    contenido: Optional[Any] = None
    creado_en: datetime

    class Config:
        from_attributes = True


class ResumenSeleccionCreate(BaseModel):
    titulo: Optional[str] = None
    audio_ids: list[int]
    tipo_resumen: str = Field("MEDIO", pattern="^(CORTO|MEDIO|DETALLADO)$")


class ResumenManualCreate(BaseModel):
    titulo: str
    texto: str
    tipo_resumen: str = "MEDIO"
    audio_ids: Optional[list[int]] = None