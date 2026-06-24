from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text

from app.models.plan import Plan
from app.models.suscripcion import Suscripcion
from app.models.usuario import Usuario
from app.schemas.plan import PlanCreate, PlanUpdate


# ─── Utilidades ──────────────────────────────────────────────────────────────

def _verificar_admin(db: Session, usuario_id: int):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or usuario.rol != "ADMIN":
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")


# ─── Planes ──────────────────────────────────────────────────────────────────

def listar_planes(db: Session, solo_activos: bool = True) -> list[Plan]:
    q = db.query(Plan)
    if solo_activos:
        q = q.filter(Plan.activo == True)
    return q.order_by(Plan.precio.asc()).all()


def obtener_plan_por_id(db: Session, plan_id: int) -> Plan:
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan


def crear_plan(db: Session, usuario_id: int, data: PlanCreate) -> Plan:
    _verificar_admin(db, usuario_id)

    existente = db.query(Plan).filter(Plan.nombre == data.nombre).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un plan con ese nombre")

    plan = Plan(
        nombre=data.nombre,
        descripcion=data.descripcion,
        precio=data.precio,
        max_audios=data.max_audios,
        max_proyectos=data.max_proyectos,
        max_transcripciones=data.max_transcripciones,
        max_resumenes=data.max_resumenes,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def actualizar_plan(db: Session, usuario_id: int, plan_id: int, data: PlanUpdate) -> Plan:
    _verificar_admin(db, usuario_id)
    plan = obtener_plan_por_id(db, plan_id)

    if data.nombre is not None:
        otro = db.query(Plan).filter(Plan.nombre == data.nombre, Plan.id != plan_id).first()
        if otro:
            raise HTTPException(status_code=400, detail="Ya existe un plan con ese nombre")
        plan.nombre = data.nombre

    if data.descripcion is not None:
        plan.descripcion = data.descripcion
    if data.precio is not None:
        plan.precio = data.precio
    if data.max_audios is not None:
        plan.max_audios = data.max_audios
    if data.max_proyectos is not None:
        plan.max_proyectos = data.max_proyectos
    if data.max_transcripciones is not None:
        plan.max_transcripciones = data.max_transcripciones
    if data.max_resumenes is not None:
        plan.max_resumenes = data.max_resumenes
    if data.activo is not None:
        plan.activo = data.activo

    db.commit()
    db.refresh(plan)
    return plan


def desactivar_plan(db: Session, usuario_id: int, plan_id: int) -> Plan:
    _verificar_admin(db, usuario_id)
    plan = obtener_plan_por_id(db, plan_id)

    subs_activas = (
        db.query(Suscripcion)
        .filter(Suscripcion.id_plan == plan_id, Suscripcion.estado == "ACTIVA")
        .count()
    )
    # Sólo bloqueamos eliminar; desactivar sí está permitido aunque haya subs
    plan.activo = False
    db.commit()
    db.refresh(plan)
    return plan


def activar_plan(db: Session, usuario_id: int, plan_id: int) -> Plan:
    _verificar_admin(db, usuario_id)
    plan = obtener_plan_por_id(db, plan_id)
    plan.activo = True
    db.commit()
    db.refresh(plan)
    return plan


# ─── Suscripciones ───────────────────────────────────────────────────────────

def obtener_suscripcion_activa(db: Session, usuario_id: int) -> Optional[Suscripcion]:
    return (
        db.query(Suscripcion)
        .filter(Suscripcion.id_usuario == usuario_id, Suscripcion.estado == "ACTIVA")
        .first()
    )


def asegurar_suscripcion_gratuita(db: Session, usuario_id: int):
    """Crea la suscripción al plan Gratuito si el usuario no tiene ninguna."""
    sub_activa = obtener_suscripcion_activa(db, usuario_id)
    if sub_activa:
        return sub_activa

    plan_gratuito = (
        db.query(Plan)
        .filter(Plan.nombre.ilike("gratuito"), Plan.activo == True)
        .first()
    )
    if not plan_gratuito:
        # Si todavía no existe plan gratuito, buscar el de menor precio
        plan_gratuito = (
            db.query(Plan)
            .filter(Plan.activo == True)
            .order_by(Plan.precio.asc())
            .first()
        )
    if not plan_gratuito:
        return None

    nueva_sub = Suscripcion(
        id_usuario=usuario_id,
        id_plan=plan_gratuito.id,
        estado="ACTIVA"
    )
    db.add(nueva_sub)
    db.commit()
    db.refresh(nueva_sub)
    return nueva_sub


def cambiar_plan_usuario(db: Session, usuario_id: int, plan_id: int) -> Suscripcion:
    plan = obtener_plan_por_id(db, plan_id)
    if not plan.activo:
        raise HTTPException(status_code=400, detail="El plan seleccionado no está disponible")

    # Desactivar suscripción anterior
    sub_anterior = obtener_suscripcion_activa(db, usuario_id)
    if sub_anterior:
        sub_anterior.estado = "CANCELADA"
        sub_anterior.fecha_fin = datetime.now(timezone.utc)

    nueva_sub = Suscripcion(
        id_usuario=usuario_id,
        id_plan=plan_id,
        estado="ACTIVA"
    )
    db.add(nueva_sub)
    db.commit()
    db.refresh(nueva_sub)
    return nueva_sub


def cancelar_suscripcion(db: Session, usuario_id: int) -> Suscripcion:
    sub = obtener_suscripcion_activa(db, usuario_id)
    if not sub:
        raise HTTPException(status_code=404, detail="No tienes una suscripción activa")

    sub.estado = "CANCELADA"
    sub.fecha_fin = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sub)
    return sub


def listar_suscripciones(db: Session, usuario_id: int) -> list[Suscripcion]:
    """Admin: todas las suscripciones activas del sistema."""
    _verificar_admin(db, usuario_id)
    return (
        db.query(Suscripcion)
        .filter(Suscripcion.estado == "ACTIVA")
        .order_by(Suscripcion.fecha_inicio.desc())
        .all()
    )


def historial_suscripciones_usuario(db: Session, usuario_id: int) -> list[Suscripcion]:
    return (
        db.query(Suscripcion)
        .filter(Suscripcion.id_usuario == usuario_id)
        .order_by(Suscripcion.creado_en.desc())
        .all()
    )


# ─── Usuarios (Admin) ────────────────────────────────────────────────────────

def listar_usuarios_admin(db: Session, admin_id: int, busqueda: Optional[str] = None) -> list[Usuario]:
    _verificar_admin(db, admin_id)
    q = db.query(Usuario)
    if busqueda:
        termino = f"%{busqueda}%"
        q = q.filter(
            (Usuario.nombre_completo.ilike(termino)) |
            (Usuario.correo.ilike(termino))
        )
    return q.order_by(Usuario.fecha_creacion.desc()).all()


def cambiar_estado_usuario(db: Session, admin_id: int, usuario_id: int, activar: bool) -> Usuario:
    _verificar_admin(db, admin_id)
    if admin_id == usuario_id:
        raise HTTPException(status_code=400, detail="No puedes cambiar el estado de tu propia cuenta")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.estado = activar
    db.commit()
    db.refresh(usuario)
    return usuario


# ─── Métricas ────────────────────────────────────────────────────────────────

def obtener_metricas(db: Session, admin_id: int, fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None):
    _verificar_admin(db, admin_id)

    filtro_fechas = ""
    params: dict = {}

    if fecha_inicio and fecha_fin:
        filtro_fechas = "WHERE creado_en::date BETWEEN :fi AND :ff"
        params = {"fi": fecha_inicio, "ff": fecha_fin}
    elif fecha_inicio:
        filtro_fechas = "WHERE creado_en::date >= :fi"
        params = {"fi": fecha_inicio}
    elif fecha_fin:
        filtro_fechas = "WHERE creado_en::date <= :ff"
        params = {"ff": fecha_fin}

    def count_table(table: str) -> int:
        query_str = f"SELECT COUNT(*) FROM {table} {filtro_fechas}" if filtro_fechas else f"SELECT COUNT(*) FROM {table}"
        result = db.execute(sql_text(query_str), params).scalar()
        return result or 0

    # Conteos generales
    total_usuarios = db.execute(sql_text("SELECT COUNT(*) FROM usuario")).scalar() or 0
    usuarios_activos = db.execute(sql_text("SELECT COUNT(*) FROM usuario WHERE estado = TRUE")).scalar() or 0
    total_proyectos = count_table("proyecto")
    total_audios = count_table("audio")
    audios_completados = db.execute(
        sql_text(f"SELECT COUNT(*) FROM audio {filtro_fechas + (' AND ' if filtro_fechas else 'WHERE ')}estado_procesamiento = 'COMPLETADO'" if filtro_fechas else "SELECT COUNT(*) FROM audio WHERE estado_procesamiento = 'COMPLETADO'"),
        params
    ).scalar() or 0
    total_transcripciones = count_table("transcripcion")
    total_resumenes = count_table("resumen")
    total_quizzes = db.execute(sql_text("SELECT COUNT(*) FROM quizzes")).scalar() or 0
    total_presentaciones = count_table("presentacion")
    total_grafos = count_table("grafo")
    total_conversaciones = count_table("chat_conversacion")
    total_mensajes = count_table("chat_mensaje")
    suscripciones_activas = db.execute(sql_text("SELECT COUNT(*) FROM suscripcion WHERE estado = 'ACTIVA'")).scalar() or 0

    # Distribución por plan
    distribucion_planes = db.execute(sql_text("""
        SELECT p.nombre, COUNT(s.id) as total
        FROM plan p
        LEFT JOIN suscripcion s ON s.id_plan = p.id AND s.estado = 'ACTIVA'
        GROUP BY p.nombre
        ORDER BY total DESC
    """)).fetchall()

    return {
        "usuarios": {
            "total": total_usuarios,
            "activos": usuarios_activos,
            "inactivos": total_usuarios - usuarios_activos,
        },
        "proyectos": total_proyectos,
        "audios": {
            "total": total_audios,
            "completados": audios_completados,
            "pendientes": total_audios - audios_completados,
        },
        "transcripciones": total_transcripciones,
        "contenido_ia": {
            "resumenes": total_resumenes,
            "quizzes": total_quizzes,
            "presentaciones": total_presentaciones,
            "grafos": total_grafos,
        },
        "chat": {
            "conversaciones": total_conversaciones,
            "mensajes": total_mensajes,
        },
        "suscripciones_activas": suscripciones_activas,
        "distribucion_planes": [
            {"plan": row.nombre, "usuarios": row.total}
            for row in distribucion_planes
        ],
    }
