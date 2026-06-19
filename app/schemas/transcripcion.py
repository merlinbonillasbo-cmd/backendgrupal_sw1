from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TranscripcionOut(BaseModel):
    id: int
    id_audio: int
    modelo_usado: Optional[str] = None
    cantidad_palabras: Optional[int] = None
    texto_generado: Optional[str] = None
    fecha_creado: datetime

    class Config:
        from_attributes = True