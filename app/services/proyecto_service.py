from sqlalchemy.orm import Session

from app.models.proyecto import Proyecto
from app.schemas.proyecto import ProyectoCreate, ProyectoUpdate


def crear_proyecto(db: Session, data: ProyectoCreate, usuario_id: int) -> Proyecto:
    nuevo_proyecto = Proyecto(
        id_usuario=usuario_id,
        nombre=data.nombre,
        descripcion=data.descripcion
    )

    db.add(nuevo_proyecto)
    db.commit()
    db.refresh(nuevo_proyecto)

    return nuevo_proyecto


def listar_proyectos_usuario(db: Session, usuario_id: int):
    return (
        db.query(Proyecto)
        .filter(Proyecto.id_usuario == usuario_id)
        .order_by(Proyecto.creado_en.desc())
        .all()
    )


def obtener_proyecto_por_id(db: Session, proyecto_id: int, usuario_id: int):
    return (
        db.query(Proyecto)
        .filter(
            Proyecto.id == proyecto_id,
            Proyecto.id_usuario == usuario_id
        )
        .first()
    )


def actualizar_proyecto(db: Session, proyecto: Proyecto, data: ProyectoUpdate) -> Proyecto:
    if data.nombre is not None:
        proyecto.nombre = data.nombre

    if data.descripcion is not None:
        proyecto.descripcion = data.descripcion

    db.commit()
    db.refresh(proyecto)

    return proyecto


def eliminar_proyecto(db: Session, proyecto: Proyecto) -> None:
    db.delete(proyecto)
    db.commit()