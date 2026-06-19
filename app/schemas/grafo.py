from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class GrafoCreate(BaseModel):
    nivel_detalle: str = Field(default="MEDIO", pattern="^(BASICO|MEDIO|AVANZADO)$")


class GrafoOut(BaseModel):
    id: int
    id_proyecto: int
    id_usuario: int
    id_solicitud: Optional[int] = None

    titulo: Optional[str] = None
    descripcion: Optional[str] = None

    contenido: Any
    modelo_usado: Optional[str] = None

    cantidad_nodos: int = 0
    cantidad_relaciones: int = 0

    creado_en: datetime

    class Config:
        from_attributes = True