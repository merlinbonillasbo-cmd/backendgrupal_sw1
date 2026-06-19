from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    descripcion: Optional[str] = None


class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    descripcion: Optional[str] = None


class ProyectoOut(BaseModel):
    id: int
    id_usuario: int
    nombre: str
    descripcion: Optional[str] = None
    creado_en: datetime

    class Config:
        from_attributes = True