from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AudioBase(BaseModel):
    titulo: str

class AudioCreate(AudioBase):
    pass

class AudioOut(AudioBase):
    id: int
    id_proyecto: int
    url_audio: str
    estado_procesamiento: str
    mensaje_error: Optional[str] = None
    creado_en: datetime

    class Config:
        from_attributes = True
