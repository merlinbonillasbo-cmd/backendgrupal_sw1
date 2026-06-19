from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.db import get_db
from app.models.proyecto import Proyecto
from app.schemas.proyecto import ProyectoCreate, ProyectoOut
from app.core.security import verify_token

proyecto_router = APIRouter()

# 1. CREAR PROYECTO (Requiere Token)
@proyecto_router.post("/", response_model=ProyectoOut)
def crear_proyecto(data: ProyectoCreate, db: Session = Depends(get_db), usuario_id: int = Depends(verify_token)):
    try:
        nuevo = Proyecto(
            nombre=data.nombre,
            descripcion=data.descripcion,
            id_usuario=usuario_id
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

# 2. LISTAR PROYECTOS DEL USUARIO (Requiere Token)
@proyecto_router.get("/", response_model=list[ProyectoOut])
def listar_proyectos(db: Session = Depends(get_db), usuario_id: int = Depends(verify_token)):
    try:
        proyectos = db.query(Proyecto).filter(Proyecto.id_usuario == usuario_id).order_by(Proyecto.id.asc()).all()
        return proyectos
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

# 3. ELIMINAR PROYECTO (Requiere Token)
@proyecto_router.delete("/{id}")
def eliminar_proyecto(id: int, db: Session = Depends(get_db), usuario_id: int = Depends(verify_token)):
    try:
        proyecto = db.query(Proyecto).filter(Proyecto.id == id, Proyecto.id_usuario == usuario_id).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado o no autorizado")
        db.delete(proyecto)
        db.commit()
        return {"mensaje": "Proyecto eliminado exitosamente"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

# 4. EDITAR PROYECTO (Requiere Token)
@proyecto_router.put("/{id}", response_model=ProyectoOut)
def editar_proyecto(id: int, data: ProyectoCreate, db: Session = Depends(get_db), usuario_id: int = Depends(verify_token)):
    try:
        proyecto = db.query(Proyecto).filter(Proyecto.id == id, Proyecto.id_usuario == usuario_id).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado o no autorizado")
        
        proyecto.nombre = data.nombre
        proyecto.descripcion = data.descripcion
        
        db.commit()
        db.refresh(proyecto)
        return proyecto
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
