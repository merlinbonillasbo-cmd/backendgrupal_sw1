from sqlalchemy import Column, Integer, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database.connection import Base


class FragmentoTranscripcion(Base):
    __tablename__ = "fragmento_transcripcion"

    id = Column(Integer, primary_key=True, index=True)

    id_transcripcion = Column(
        Integer,
        ForeignKey("transcripcion.id", ondelete="CASCADE"),
        nullable=False
    )

    indice_fragmento = Column(Integer, nullable=False)
    texto_fragmento = Column(Text, nullable=False)

    embedding = Column(Vector(768), nullable=True)

    creado_en = Column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        nullable=False
    )

    transcripcion = relationship("Transcripcion")
