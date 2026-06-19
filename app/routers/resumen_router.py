from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import StreamingResponse

from app.database.connection import get_db
from app.core.security import verify_token
from app.schemas.resumen import ResumenCreate, ResumenOut
from app.services.resumen_service import (
    generar_resumen_de_audio,
    generar_resumen_de_proyecto,
    obtener_ultimo_resumen_audio,
    obtener_ultimo_resumen_proyecto,
    obtener_resumen_por_id_usuario,
    listar_resumenes_por_proyecto,
    listar_resumenes_por_audio,
    generar_archivo_txt,
    generar_archivo_pdf,
    generar_archivo_word
)


resumen_router = APIRouter(
    prefix="/api/resumenes",
    tags=["Resúmenes"]
)


@resumen_router.post("/audio/{audio_id}", response_model=ResumenOut)
def resumen_audio(
    audio_id: int,
    data: ResumenCreate,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return generar_resumen_de_audio(
            db=db,
            audio_id=audio_id,
            usuario_id=usuario_id,
            tipo_resumen=data.tipo_resumen
        )

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


@resumen_router.post("/proyecto/{proyecto_id}", response_model=ResumenOut)
def resumen_proyecto(
    proyecto_id: int,
    data: ResumenCreate,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return generar_resumen_de_proyecto(
            db=db,
            proyecto_id=proyecto_id,
            usuario_id=usuario_id,
            tipo_resumen=data.tipo_resumen
        )

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
    
@resumen_router.get("/audio/{audio_id}", response_model=ResumenOut)
def ver_resumen_audio(
    audio_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return obtener_ultimo_resumen_audio(
            db=db,
            audio_id=audio_id,
            usuario_id=usuario_id
        )

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


@resumen_router.get("/proyecto/{proyecto_id}", response_model=ResumenOut)
def ver_resumen_proyecto(
    proyecto_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return obtener_ultimo_resumen_proyecto(
            db=db,
            proyecto_id=proyecto_id,
            usuario_id=usuario_id
        )

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
    
@resumen_router.get("/proyecto/{proyecto_id}/historial", response_model=list[ResumenOut])
def historial_resumenes_proyecto(
    proyecto_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_resumenes_por_proyecto(
            db=db,
            proyecto_id=proyecto_id,
            usuario_id=usuario_id
        )

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


@resumen_router.get("/audio/{audio_id}/historial", response_model=list[ResumenOut])
def historial_resumenes_audio(
    audio_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return listar_resumenes_por_audio(
            db=db,
            audio_id=audio_id,
            usuario_id=usuario_id
        )

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


@resumen_router.get("/{resumen_id}", response_model=ResumenOut)
def ver_resumen_por_id(
    resumen_id: int,
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        return obtener_resumen_por_id_usuario(
            db=db,
            resumen_id=resumen_id,
            usuario_id=usuario_id
        )

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


@resumen_router.get("/{resumen_id}/descargar")
def descargar_resumen(
    resumen_id: int,
    formato: str = "txt",
    usuario_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        resumen = obtener_resumen_por_id_usuario(
            db=db,
            resumen_id=resumen_id,
            usuario_id=usuario_id
        )

        formato = formato.lower()

        nombre_base = f"resumen_{resumen.id}"

        if formato == "txt":
            archivo = generar_archivo_txt(resumen)
            media_type = "text/plain"
            filename = f"{nombre_base}.txt"

        elif formato == "pdf":
            archivo = generar_archivo_pdf(resumen)
            media_type = "application/pdf"
            filename = f"{nombre_base}.pdf"

        elif formato in ["docx", "word"]:
            archivo = generar_archivo_word(resumen)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{nombre_base}.docx"

        else:
            raise HTTPException(
                status_code=400,
                detail="Formato no permitido. Usa txt, pdf o docx."
            )

        return StreamingResponse(
            archivo,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

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