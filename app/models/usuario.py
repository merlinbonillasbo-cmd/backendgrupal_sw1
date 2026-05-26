from sqlalchemy import Column, Integer, String, Boolean, text, TIMESTAMP
from app.core.db import Base

class Usuario(Base):
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(200), nullable=False)
    correo = Column(String(254), unique=True, nullable=False, index=True)
    contrasena = Column(String, nullable=False)
    estado = Column(Boolean, nullable=False, server_default="true")
    fecha_creacion = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))