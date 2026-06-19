from pydantic import BaseModel
from datetime import datetime

class ProyectoBase(BaseModel):
    nombre: str
    descripcion: str | None = None

class ProyectoCreate(ProyectoBase):
    pass

class ProyectoOut(ProyectoBase):
    id: int
    id_usuario: int
    creado_en: datetime

    class Config:
        from_attributes = True
