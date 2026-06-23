from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Presentacion(Base):
    __tablename__ = "presentacion"

    id = Column(Integer, primary_key=True, index=True)
    id_solicitud = Column(
        Integer,
        ForeignKey("solicitud.id", ondelete="CASCADE"),
        nullable=False
    )
    titulo = Column(String(200), nullable=True)
    ruta = Column(Text, nullable=True)  # Se utilizará para guardar preferencias de diseño
    contenido = Column(JSON, nullable=True)  # Estructura de las diapositivas
    cantidad_diapositivas = Column(Integer, nullable=True)
    creado_en = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    solicitud = relationship("Solicitud")
