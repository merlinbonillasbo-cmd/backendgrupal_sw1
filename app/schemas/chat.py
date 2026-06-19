from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatPreguntaCreate(BaseModel):
    pregunta: str = Field(..., min_length=2)
    id_conversacion: Optional[int] = None


class ChatConversacionOut(BaseModel):
    id: int
    id_usuario: int
    id_proyecto: Optional[int] = None
    titulo: Optional[str] = None
    creado_en: datetime

    class Config:
        from_attributes = True


class ChatMensajeOut(BaseModel):
    id: int
    id_conversacion: int
    rol: str
    contenido: str
    creado_en: datetime

    class Config:
        from_attributes = True


class ChatRespuestaOut(BaseModel):
    conversacion: ChatConversacionOut
    pregunta: ChatMensajeOut
    respuesta: ChatMensajeOut