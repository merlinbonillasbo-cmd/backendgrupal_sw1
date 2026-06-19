from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, Interval, text
from sqlalchemy.orm import relationship
from app.core.db import Base

class Audio(Base):
    __tablename__ = "audio"

    id = Column(Integer, primary_key=True, index=True)
    id_proyecto = Column(Integer, ForeignKey("proyecto.id", ondelete="CASCADE"), nullable=False)
    titulo = Column(String(200), nullable=False)
    url_audio = Column(Text, nullable=False)
    duracion = Column(Interval, nullable=True)
    estado_procesamiento = Column(String(30), nullable=False, server_default="PENDIENTE")
    mensaje_error = Column(Text, nullable=True)
    creado_en = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    proyecto = relationship("Proyecto")
