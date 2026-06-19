from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class ChatMensaje(Base):
    __tablename__ = "chat_mensaje"

    id = Column(Integer, primary_key=True, index=True)

    id_conversacion = Column(
        Integer,
        ForeignKey("chat_conversacion.id", ondelete="CASCADE"),
        nullable=False
    )

    rol = Column(String(20), nullable=False)
    contenido = Column(Text, nullable=False)

    creado_en = Column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        nullable=False
    )

    conversacion = relationship("ChatConversacion")