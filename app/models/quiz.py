from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)

    id_solicitud = Column(
        Integer,
        ForeignKey("solicitud.id", ondelete="CASCADE"),
        nullable=False
    )

    titulo = Column(String(200), nullable=True)
    total_preguntas = Column(Integer, nullable=False, default=0)
    url_archivo = Column(Text, nullable=True)
    creado_en = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    solicitud = relationship("Solicitud")
    preguntas = relationship("PreguntaQuiz", back_populates="quiz", cascade="all, delete-orphan")


class PreguntaQuiz(Base):
    __tablename__ = "preguntas_quizzes"

    id = Column(Integer, primary_key=True, index=True)

    id_quizzes = Column(
        Integer,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False
    )

    indice_pregunta = Column(Integer, nullable=False)
    texto_pregunta = Column(Text, nullable=False)
    texto_respuesta = Column(Text, nullable=False)

    quiz = relationship("Quiz", back_populates="preguntas")
