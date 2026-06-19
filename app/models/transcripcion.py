from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Transcripcion(Base):
    __tablename__ = "transcripcion"

    id = Column(Integer, primary_key=True, index=True)

    id_audio = Column(
        Integer,
        ForeignKey("audio.id", ondelete="CASCADE"),
        nullable=False
    )

    modelo_usado = Column(String(100), nullable=True)
    cantidad_palabras = Column(Integer, nullable=True)
    texto_generado = Column(Text, nullable=True)

    fecha_creado = Column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        nullable=False
    )

    audio = relationship("Audio")