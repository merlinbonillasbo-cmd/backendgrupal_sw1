from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.db import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioLogin, UsuarioUpdate
from app.services.auth import hash_password, verify_password
from app.core.security import create_access_token, verify_token

user_router = APIRouter()


@user_router.post("/registro/", response_model=UsuarioOut)
def registrar_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        usuario = db.query(Usuario).filter(Usuario.correo == data.correo).first()
        if usuario:
            raise HTTPException(status_code=400, detail="El correo ya está registrado")
            
        nuevo = Usuario(
            nombre_completo=data.nombre_completo,
            correo=data.correo,
            contrasena=hash_password(data.contrasena) # Tu nueva función moderna con bcrypt directo
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


# 2. LOGIN (Normalizado con '/' al final)
@user_router.post("/login/")
def login(data: UsuarioLogin, db: Session = Depends(get_db)):
    try:
        usuario = db.query(Usuario).filter(Usuario.correo == data.correo).first()
        if not usuario or not verify_password(data.contrasena, usuario.contrasena):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        token = create_access_token(data={"sub": str(usuario.id)})
        return {
            "mensaje": "Login exitoso", 
            "usuario": usuario.nombre_completo, 
            "access_token": token, 
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        print("❌ ERROR CRÍTICO EN LOGIN:", str(e)) # 🌟 Esto imprimirá el culpable real en tu consola de comandos
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


# 3. VER PERFIL (Normalizado con '/' al final y consulta moderna)
@user_router.get("/perfil/", response_model=UsuarioOut)
def perfil(usuario_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    try:
        # Actualizado a filter para cumplir con los estándares modernos de SQLAlchemy
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return usuario
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


# 4. EDITAR PERFIL (Normalizado con '/' al final y consulta moderna)
@user_router.put("/perfil/", response_model=UsuarioOut)
def actualizar_usuario(
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(verify_token)
):
    try:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if data.nombre_completo:
            usuario.nombre_completo = data.nombre_completo
            
        db.commit()
        db.refresh(usuario)
        return usuario
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")