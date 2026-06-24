from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, TIMESTAMP, text
from app.database.connection import Base


class Plan(Base):
    __tablename__ = "plan"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    precio = Column(Numeric(10, 2), nullable=False, default=0)

    # Límites de uso
    max_audios = Column(Integer, nullable=True)          # None = ilimitado
    max_proyectos = Column(Integer, nullable=True)
    max_transcripciones = Column(Integer, nullable=True)
    max_resumenes = Column(Integer, nullable=True)

    activo = Column(Boolean, nullable=False, server_default=text("true"))
    creado_en = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
