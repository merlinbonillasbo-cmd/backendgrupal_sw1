from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Grafo(Base):
    __tablename__ = "grafo"

    id = Column(Integer, primary_key=True, index=True)

    id_proyecto = Column(
        Integer,
        ForeignKey("proyecto.id", ondelete="CASCADE"),
        nullable=False
    )

    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False
    )

    id_solicitud = Column(
        Integer,
        ForeignKey("solicitud.id", ondelete="SET NULL"),
        nullable=True
    )

    titulo = Column(String(200), nullable=True)
    descripcion = Column(Text, nullable=True)

    contenido = Column(JSONB, nullable=False)

    modelo_usado = Column(String(100), nullable=True)

    cantidad_nodos = Column(Integer, nullable=False, server_default="0")
    cantidad_relaciones = Column(Integer, nullable=False, server_default="0")

    creado_en = Column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        nullable=False
    )

    proyecto = relationship("Proyecto")
    usuario = relationship("Usuario")
    solicitud = relationship("Solicitud")