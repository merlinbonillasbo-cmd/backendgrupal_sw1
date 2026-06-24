from sqlalchemy import Column, Integer, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class FragmentoTranscripcion(Base):
    __tablename__ = "fragmento_transcripcion"

    id = Column(Integer, primary_key=True, index=True)

    id_transcripcion = Column(
        Integer,
        ForeignKey("transcripcion.id", ondelete="CASCADE"),
        nullable=False
    )

    #id_hablante = Column(
    #    Integer,
    #    ForeignKey("hablante.id", ondelete="SET NULL"),
    #    nullable=True
    #)

    indice_fragmento = Column(Integer, nullable=False)
    texto_fragmento = Column(Text, nullable=False)

    creado_en = Column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        nullable=False
    )

    transcripcion = relationship("Transcripcion")
