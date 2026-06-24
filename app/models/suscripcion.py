from sqlalchemy import Column, Integer, String, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Suscripcion(Base):
    __tablename__ = "suscripcion"

    id = Column(Integer, primary_key=True, index=True)

    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False
    )

    id_plan = Column(
        Integer,
        ForeignKey("plan.id", ondelete="RESTRICT"),
        nullable=False
    )

    estado = Column(String(30), nullable=False, server_default="ACTIVA")  # ACTIVA | CANCELADA | EXPIRADA
    fecha_inicio = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    fecha_fin = Column(TIMESTAMP(timezone=True), nullable=True)
    creado_en = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    usuario = relationship("Usuario")
    plan = relationship("Plan")
