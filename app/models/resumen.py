from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Resumen(Base):
    __tablename__ = "resumen"

    id = Column(Integer, primary_key=True, index=True)

    id_solicitud = Column(
        Integer,
        ForeignKey("solicitud.id", ondelete="CASCADE"),
        nullable=False
    )

    titulo = Column(String(200), nullable=True)
    tipo_resumen = Column(String(20), nullable=False)
    ruta = Column(Text, nullable=True)
    contenido = Column(JSONB, nullable=True)
    creado_en = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    solicitud = relationship("Solicitud")