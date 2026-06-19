import json
import re

from fastapi import HTTPException
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from app.core.config import settings
from app.models.proyecto import Proyecto
from app.models.audio import Audio
from app.models.transcripcion import Transcripcion
from app.models.grafo import Grafo


MODELO_GRAFO = "gemini-2.5-flash"


def verificar_proyecto_usuario(
    db: Session,
    proyecto_id: int,
    usuario_id: int
) -> Proyecto:
    proyecto = (
        db.query(Proyecto)
        .filter(
            Proyecto.id == proyecto_id,
            Proyecto.id_usuario == usuario_id
        )
        .first()
    )

    if not proyecto:
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado"
        )

    return proyecto


def obtener_transcripciones_proyecto(
    db: Session,
    proyecto_id: int,
    usuario_id: int
):
    verificar_proyecto_usuario(db, proyecto_id, usuario_id)

    resultados = (
        db.query(Audio, Transcripcion)
        .join(Transcripcion, Transcripcion.id_audio == Audio.id)
        .filter(Audio.id_proyecto == proyecto_id)
        .order_by(Audio.creado_en.asc())
        .all()
    )

    transcripciones_validas = []

    for audio, transcripcion in resultados:
        if transcripcion.texto_generado and transcripcion.texto_generado.strip():
            transcripciones_validas.append((audio, transcripcion))

    if not transcripciones_validas:
        raise HTTPException(
            status_code=400,
            detail="El proyecto no tiene audios transcritos para generar el grafo"
        )

    return transcripciones_validas


def construir_contexto_grafo(transcripciones) -> str:
    partes = []

    for index, (audio, transcripcion) in enumerate(transcripciones, start=1):
        partes.append(
            f"""
[AUDIO {index}]
Título: {audio.titulo}
Fecha: {audio.creado_en}

Transcripción:
{transcripcion.texto_generado}
"""
        )

    return "\n\n---\n\n".join(partes)


def cantidad_por_nivel(nivel_detalle: str):
    if nivel_detalle == "BASICO":
        return 10, 15

    if nivel_detalle == "AVANZADO":
        return 28, 45

    return 18, 30


def crear_prompt_grafo(contexto: str, nivel_detalle: str) -> str:
    max_nodos, max_relaciones = cantidad_por_nivel(nivel_detalle)

    return f"""
Eres un experto en análisis de conocimiento, mapas conceptuales y extracción de relaciones semánticas.

Tu tarea es analizar transcripciones de audios de un proyecto y generar un grafo de conceptos clave.

Nivel de detalle: {nivel_detalle}
Máximo de nodos: {max_nodos}
Máximo de relaciones: {max_relaciones}

Debes devolver únicamente JSON válido. No uses markdown. No uses ```json.

Estructura obligatoria:

{{
  "titulo": "Mapa conceptual del proyecto",
  "descripcion": "Descripción breve del conocimiento encontrado",
  "nodos": [
    {{
      "id": "concepto_unico_en_minusculas",
      "label": "Nombre visible",
      "tipo": "TEMA|SUBTEMA|CONCEPTO|PERSONA|TAREA|DECISION|RECURSO",
      "importancia": 1,
      "descripcion": "Explicación breve del nodo",
      "audio_origen": "Título del audio donde aparece principalmente"
    }}
  ],
  "relaciones": [
    {{
      "id": "relacion_1",
      "source": "id_nodo_origen",
      "target": "id_nodo_destino",
      "label": "se relaciona con",
      "tipo": "CAUSA|PARTE_DE|RELACIONADO|DEPENDE_DE|GENERA|USA|MENCIONA|DECIDE|ASIGNA",
      "peso": 1
    }}
  ],
  "insights": [
    "Conclusión importante 1",
    "Conclusión importante 2"
  ],
  "recomendaciones": [
    "Recomendación útil 1",
    "Recomendación útil 2"
  ]
}}

Reglas:
- Usa solo información presente en las transcripciones.
- No inventes nombres, decisiones ni tareas.
- Los ids de nodos deben ser únicos, en minúsculas, sin espacios, sin tildes, usando guiones bajos.
- Toda relación debe conectar nodos existentes.
- La importancia debe ir del 1 al 5.
- El peso de relación debe ir del 1 al 5.
- Evita conceptos demasiado genéricos como "tema", "audio", "información".
- Prioriza conceptos que ayuden a comprender el proyecto.
- Si hay tareas o decisiones explícitas, inclúyelas como nodos tipo TAREA o DECISION.
- No agregues comas finales al último elemento de objetos o arreglos.
- Todas las propiedades deben tener comillas dobles.
- No uses comentarios.
- No uses texto fuera del JSON.
- Devuelve solo JSON válido.

Transcripciones del proyecto:
{contexto}
"""


def limpiar_json_basico(texto: str) -> str:
    limpio = texto.strip()

    limpio = limpio.replace("```json", "").replace("```", "").strip()

    # Elimina comas sobrantes antes de cerrar objetos o listas:
    # Ejemplo: {"a": 1,} -> {"a": 1}
    # Ejemplo: [1,2,] -> [1,2]
    limpio = re.sub(r",\s*([}\]])", r"\1", limpio)

    return limpio


def extraer_json_desde_respuesta(texto: str) -> dict:
    if not texto or not texto.strip():
        raise HTTPException(
            status_code=500,
            detail="Gemini no devolvió contenido para el grafo"
        )

    limpio = limpiar_json_basico(texto)

    try:
        return json.loads(limpio)

    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", limpio, re.DOTALL)

        if not match:
            raise HTTPException(
                status_code=500,
                detail="No se pudo interpretar la respuesta de Gemini como JSON"
            )

        fragmento = limpiar_json_basico(match.group(0))

        try:
            return json.loads(fragmento)

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"JSON inválido generado por Gemini: {str(e)}"
            )


def normalizar_id(valor: str) -> str:
    valor = valor.lower().strip()
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n"
    }

    for origen, destino in reemplazos.items():
        valor = valor.replace(origen, destino)

    valor = re.sub(r"[^a-z0-9_]+", "_", valor)
    valor = re.sub(r"_+", "_", valor).strip("_")

    return valor or "concepto"


def validar_y_limpiar_grafo(data: dict) -> dict:
    nodos_originales = data.get("nodos", [])
    relaciones_originales = data.get("relaciones", [])

    if not isinstance(nodos_originales, list) or not nodos_originales:
        raise HTTPException(
            status_code=500,
            detail="El grafo generado no contiene nodos válidos"
        )

    nodos = []
    ids_usados = set()

    for index, nodo in enumerate(nodos_originales, start=1):
        label = str(nodo.get("label") or f"Concepto {index}").strip()
        base_id = normalizar_id(str(nodo.get("id") or label))

        node_id = base_id
        contador = 2

        while node_id in ids_usados:
            node_id = f"{base_id}_{contador}"
            contador += 1

        ids_usados.add(node_id)

        tipo = str(nodo.get("tipo") or "CONCEPTO").upper()

        if tipo not in ["TEMA", "SUBTEMA", "CONCEPTO", "PERSONA", "TAREA", "DECISION", "RECURSO"]:
            tipo = "CONCEPTO"

        importancia = nodo.get("importancia", 3)

        try:
            importancia = int(importancia)
        except Exception:
            importancia = 3

        importancia = max(1, min(5, importancia))

        nodos.append({
            "id": node_id,
            "label": label,
            "tipo": tipo,
            "importancia": importancia,
            "descripcion": str(nodo.get("descripcion") or "").strip(),
            "audio_origen": str(nodo.get("audio_origen") or "").strip()
        })

    ids_validos = {nodo["id"] for nodo in nodos}

    relaciones = []

    for index, relacion in enumerate(relaciones_originales, start=1):
        source = normalizar_id(str(relacion.get("source") or ""))
        target = normalizar_id(str(relacion.get("target") or ""))

        if source not in ids_validos or target not in ids_validos or source == target:
            continue

        tipo = str(relacion.get("tipo") or "RELACIONADO").upper()

        if tipo not in ["CAUSA", "PARTE_DE", "RELACIONADO", "DEPENDE_DE", "GENERA", "USA", "MENCIONA", "DECIDE", "ASIGNA"]:
            tipo = "RELACIONADO"

        peso = relacion.get("peso", 2)

        try:
            peso = int(peso)
        except Exception:
            peso = 2

        peso = max(1, min(5, peso))

        relaciones.append({
            "id": str(relacion.get("id") or f"relacion_{index}"),
            "source": source,
            "target": target,
            "label": str(relacion.get("label") or "se relaciona con").strip(),
            "tipo": tipo,
            "peso": peso
        })

    return {
        "titulo": str(data.get("titulo") or "Mapa conceptual del proyecto").strip(),
        "descripcion": str(data.get("descripcion") or "").strip(),
        "nodos": nodos,
        "relaciones": relaciones,
        "insights": data.get("insights", []) if isinstance(data.get("insights", []), list) else [],
        "recomendaciones": data.get("recomendaciones", []) if isinstance(data.get("recomendaciones", []), list) else []
    }


def generar_grafo_con_gemini(contexto: str, nivel_detalle: str) -> dict:
    client = genai.Client(api_key=settings.gemini_api_key)

    prompt = crear_prompt_grafo(contexto, nivel_detalle)

    response = client.models.generate_content(
        model=MODELO_GRAFO,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
    )

    data = extraer_json_desde_respuesta(response.text)

    return validar_y_limpiar_grafo(data)

def guardar_grafo(
    db: Session,
    proyecto_id: int,
    usuario_id: int,
    contenido: dict
) -> Grafo:
    nodos = contenido.get("nodos", [])
    relaciones = contenido.get("relaciones", [])

    grafo = Grafo(
        id_proyecto=proyecto_id,
        id_usuario=usuario_id,
        id_solicitud=None,
        titulo=contenido.get("titulo", "Mapa conceptual del proyecto"),
        descripcion=contenido.get("descripcion"),
        contenido=contenido,
        modelo_usado=MODELO_GRAFO,
        cantidad_nodos=len(nodos),
        cantidad_relaciones=len(relaciones)
    )

    db.add(grafo)
    db.commit()
    db.refresh(grafo)

    return grafo


def generar_grafo_proyecto(
    db: Session,
    proyecto_id: int,
    usuario_id: int,
    nivel_detalle: str
) -> Grafo:
    transcripciones = obtener_transcripciones_proyecto(
        db=db,
        proyecto_id=proyecto_id,
        usuario_id=usuario_id
    )

    contexto = construir_contexto_grafo(transcripciones)

    try:
        contenido = generar_grafo_con_gemini(
            contexto=contexto,
            nivel_detalle=nivel_detalle
        )

        return guardar_grafo(
            db=db,
            proyecto_id=proyecto_id,
            usuario_id=usuario_id,
            contenido=contenido
        )

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar grafo: {str(e)}"
        )


def obtener_ultimo_grafo_proyecto(
    db: Session,
    proyecto_id: int,
    usuario_id: int
) -> Grafo:
    verificar_proyecto_usuario(db, proyecto_id, usuario_id)

    grafo = (
        db.query(Grafo)
        .filter(
            Grafo.id_proyecto == proyecto_id,
            Grafo.id_usuario == usuario_id
        )
        .order_by(Grafo.creado_en.desc())
        .first()
    )

    if not grafo:
        raise HTTPException(
            status_code=404,
            detail="Este proyecto todavía no tiene grafo generado"
        )

    return grafo


def listar_grafos_proyecto(
    db: Session,
    proyecto_id: int,
    usuario_id: int
):
    verificar_proyecto_usuario(db, proyecto_id, usuario_id)

    return (
        db.query(Grafo)
        .filter(
            Grafo.id_proyecto == proyecto_id,
            Grafo.id_usuario == usuario_id
        )
        .order_by(Grafo.creado_en.desc())
        .all()
    )


def obtener_grafo_por_id(
    db: Session,
    grafo_id: int,
    usuario_id: int
) -> Grafo:
    grafo = (
        db.query(Grafo)
        .filter(
            Grafo.id == grafo_id,
            Grafo.id_usuario == usuario_id
        )
        .first()
    )

    if not grafo:
        raise HTTPException(
            status_code=404,
            detail="Grafo no encontrado"
        )

    return grafo


def eliminar_grafo_usuario(
    db: Session,
    grafo_id: int,
    usuario_id: int
):
    grafo = obtener_grafo_por_id(db, grafo_id, usuario_id)

    db.delete(grafo)
    db.commit()