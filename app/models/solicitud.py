from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Solicitud(Base):
    __tablename__ = "solicitud"

    id = Column(Integer, primary_key=True, index=True)

    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False
    )

    tipo = Column(String(50), nullable=False)
    prompt_usado = Column(Text, nullable=True)
    estado = Column(String(30), nullable=False, server_default="PENDIENTE")
    mensaje_error = Column(Text, nullable=True)
    completado_en = Column(TIMESTAMP(timezone=True), nullable=True)
    creado_en = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    usuario = relationship("Usuario")