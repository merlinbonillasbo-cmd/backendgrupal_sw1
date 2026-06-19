from sqlalchemy import Column, Integer, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class SolicitudAudio(Base):
    __tablename__ = "solicitud_audio"

    id = Column(Integer, primary_key=True, index=True)

    id_solicitud = Column(
        Integer,
        ForeignKey("solicitud.id", ondelete="CASCADE"),
        nullable=False
    )

    id_audio = Column(
        Integer,
        ForeignKey("audio.id", ondelete="CASCADE"),
        nullable=False
    )

    fecha_en = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    solicitud = relationship("Solicitud")
    audio = relationship("Audio")