from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import get_db
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioLogin
from app.services.auth_service import verify_password
from app.services.usuario_service import obtener_usuario_por_correo, crear_usuario
from app.core.security import create_access_token


auth_router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticación"]
)


@auth_router.post("/registro", response_model=UsuarioOut)
def registrar_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        usuario = obtener_usuario_por_correo(db, data.correo)

        if usuario:
            raise HTTPException(status_code=400, detail="El correo ya está registrado")

        nuevo_usuario = crear_usuario(db, data)

        return nuevo_usuario

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error en la base de datos: {str(e)}"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )


@auth_router.post("/login")
def login(data: UsuarioLogin, db: Session = Depends(get_db)):
    try:
        usuario = obtener_usuario_por_correo(db, data.correo)

        if not usuario or not verify_password(data.contrasena, usuario.contrasena):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        if not usuario.estado:
            raise HTTPException(status_code=403, detail="Usuario inactivo")

        token = create_access_token(data={"sub": str(usuario.id)})

        return {
            "mensaje": "Login exitoso",
            "usuario": {
                "id": usuario.id,
                "nombre_completo": usuario.nombre_completo,
                "correo": usuario.correo,
                "rol": usuario.rol
            },
            "access_token": token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la base de datos: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )