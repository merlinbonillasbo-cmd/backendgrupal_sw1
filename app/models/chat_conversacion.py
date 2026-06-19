from sqlalchemy import Column, Integer, String, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class ChatConversacion(Base):
    __tablename__ = "chat_conversacion"

    id = Column(Integer, primary_key=True, index=True)

    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False
    )

    id_proyecto = Column(
        Integer,
        ForeignKey("proyecto.id", ondelete="CASCADE"),
        nullable=True
    )

    titulo = Column(String(200), nullable=True)

    creado_en = Column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        nullable=False
    )

    usuario = relationship("Usuario")
    proyecto = relationship("Proyecto")