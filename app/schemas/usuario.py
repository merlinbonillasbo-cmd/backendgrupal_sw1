from pydantic import BaseModel, EmailStr

class UsuarioBase(BaseModel):
    nombre_completo: str
    correo: EmailStr
    
class UsuarioCreate(UsuarioBase):
    contrasena: str
    
class UsuarioLogin(BaseModel):
    correo: EmailStr
    contrasena: str
    
class UsuarioUpdate(BaseModel):
    nombre_completo: str | None = None
    
class UsuarioOut(UsuarioBase):
    id: int
    estado: bool
    
    class Config:
        from_attributes = True