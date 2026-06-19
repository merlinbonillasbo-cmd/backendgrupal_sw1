from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AudioOut(BaseModel):
    id: int
    id_proyecto: int
    titulo: str
    url_audio: str
    estado_procesamiento: str
    mensaje_error: Optional[str] = None
    creado_en: datetime

    class Config:
        from_attributes = True