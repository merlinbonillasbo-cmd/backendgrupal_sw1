from sqlalchemy import Column, Integer, String, Text, Numeric, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Pago(Base):
    """
    Registro de cada intento/transacción de pago simulada.
    estado: APROBADO | RECHAZADO | PENDIENTE
    """
    __tablename__ = "pago"

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

    # Identificador de transacción simulada (UUID generado en backend)
    referencia = Column(String(64), unique=True, nullable=False)

    monto = Column(Numeric(10, 2), nullable=False)
    moneda = Column(String(10), nullable=False, server_default="USD")

    # Últimos 4 dígitos de la tarjeta (nunca guardamos datos sensibles reales)
    ultimos_digitos = Column(String(4), nullable=True)
    tipo_tarjeta = Column(String(20), nullable=True)  # VISA | MASTERCARD | AMEX

    estado = Column(String(20), nullable=False, server_default="PENDIENTE")
    mensaje_respuesta = Column(Text, nullable=True)

    creado_en = Column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        nullable=False
    )

    usuario = relationship("Usuario")
    plan = relationship("Plan")
