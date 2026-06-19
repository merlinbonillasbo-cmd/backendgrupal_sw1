from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.services.auth_service import hash_password


def obtener_usuario_por_correo(db: Session, correo: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.correo == correo).first()


def obtener_usuario_por_id(db: Session, usuario_id: int) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def crear_usuario(db: Session, data: UsuarioCreate) -> Usuario:
    nuevo_usuario = Usuario(
        nombre_completo=data.nombre_completo,
        correo=data.correo,
        contrasena=hash_password(data.contrasena),
        rol="USUARIO"
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario


def actualizar_usuario(db: Session, usuario: Usuario, data: UsuarioUpdate) -> Usuario:
    if data.nombre_completo is not None:
        usuario.nombre_completo = data.nombre_completo

    db.commit()
    db.refresh(usuario)

    return usuario