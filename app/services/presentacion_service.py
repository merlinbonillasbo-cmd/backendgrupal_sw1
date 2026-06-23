import json
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from fastapi import HTTPException
from datetime import datetime, timezone

from google import genai
from app.core.config import settings
from app.models.solicitud import Solicitud
from app.models.solicitud_audio import SolicitudAudio
from app.models.presentacion import Presentacion


def listar_audios_disponibles(db: Session, usuario_id: int):
    """
    Lista todos los audios del usuario que están listos y transcritos
    para poder ser seleccionados en la generación del slide/presentación.
    """
    query = sql_text("""
        SELECT a.id, a.titulo, p.nombre AS proyecto_nombre, a.creado_en
        FROM audio a
        JOIN proyecto p ON a.id_proyecto = p.id
        JOIN transcripcion t ON t.id_audio = a.id
        WHERE p.id_usuario = :u_id AND a.estado_procesamiento = 'COMPLETADO'
        ORDER BY a.creado_en DESC
    """)
    result = db.execute(query, {"u_id": usuario_id}).fetchall()
    
    return [
        {
            "id": row.id,
            "titulo": row.titulo,
            "proyecto": row.proyecto_nombre,
            "creado_en": row.creado_en.isoformat() if row.creado_en else None
        }
        for row in result
    ]


def obtener_url_ollama_activa() -> str:
    for host in ["ollama", "localhost", "127.0.0.1"]:
        try:
            url = f"http://{host}:11434/api/tags"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return f"http://{host}:11434"
        except Exception:
            continue
    return "http://ollama:11434"


def seleccionar_modelo_ollama(active_url: str) -> str:
    try:
        url = f"{active_url}/api/tags"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            names = [m["name"] for m in models]
            generativos = [n for n in names if "embed" not in n]
            if generativos:
                for fav in ["llama3.2", "llama3", "mistral", "gemma", "phi3"]:
                    for g in generativos:
                        if fav in g:
                            return g
                return generativos[0]
    except Exception:
        pass
    return "llama3.2"


def generar_presentacion_con_ollama(prompt: str) -> str:
    active_url = obtener_url_ollama_activa()
    model = seleccionar_modelo_ollama(active_url)
    
    url = f"{active_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()["response"].strip()


def generar_presentacion_con_gemini(prompt: str) -> str:
    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()


def limpiar_y_parsear_json(texto: str) -> dict:
    limpio = texto.strip()
    if limpio.startswith("```json"):
        limpio = limpio[7:]
    elif limpio.startswith("```"):
        limpio = limpio[3:]
    if limpio.endswith("```"):
        limpio = limpio[:-3]
    limpio = limpio.strip()
    
    return json.loads(limpio)


def crear_presentacion_estudio(
    db: Session,
    usuario_id: int,
    titulo: str,
    audio_ids: list[int]
) -> dict:
    if not audio_ids:
        raise HTTPException(
            status_code=400,
            detail="Debes seleccionar al menos un audio para generar la presentación"
        )
        
    query_trans = sql_text("""
        SELECT a.titulo, t.texto_generado
        FROM audio a
        JOIN transcripcion t ON t.id_audio = a.id
        WHERE a.id IN :audio_ids AND a.id_proyecto IN (
            SELECT p.id FROM proyecto p WHERE p.id_usuario = :u_id
        )
    """)
    result = db.execute(query_trans, {"audio_ids": tuple(audio_ids), "u_id": usuario_id}).fetchall()
    
    textos_contexto = []
    for row in result:
        aud_titulo, aud_texto = row
        if aud_texto and aud_texto.strip():
            textos_contexto.append(f"Audio: {aud_titulo}\nTranscripción:\n{aud_texto}")
            
    if not textos_contexto:
        raise HTTPException(
            status_code=400,
            detail="Los audios seleccionados no cuentan con transcripciones válidas"
        )
        
    contexto = "\n\n---\n\n".join(textos_contexto)
    
    prompt = f"""
Eres un profesor universitario experto. Basándote ÚNICAMENTE en el siguiente contenido transcrito de los audios del estudiante, genera el contenido estructural para una presentación de PowerPoint de entre 5 y 7 diapositivas diseñada para estudiar el tema.

Reglas obligatorias:
1. La primera diapositiva debe tener el tipo "titulo", un título principal y un subtítulo. No debe incluir viñetas (puntos).
2. Las diapositivas restantes deben tener el tipo "contenido", un título temático específico, entre 2 y 4 puntos clave cortos (viñetas) de resumen, y una sección de notas de orador (notas_orador) que explique el contenido de forma más extensa para estudio.
3. El idioma de todo el contenido debe ser el mismo que el del texto transcrito (Español).
4. Responde ÚNICAMENTE con un objeto JSON válido, sin textos introductorios, sin bloques de código ```json, ni explicaciones externas.

Formato del JSON de respuesta esperado:
{{
  "diapositivas": [
    {{
      "tipo": "titulo",
      "titulo": "Título de la Presentación",
      "subtitulo": "Subtítulo explicativo o nombre del curso",
      "notas_orador": "Notas de introducción y bienvenida..."
    }},
    {{
      "tipo": "contenido",
      "titulo": "Título del subtema",
      "puntos": [
        "Primer punto clave resumido",
        "Segundo punto clave resumido",
        "Tercer punto clave"
      ],
      "notas_orador": "Notas detalladas de explicación de este subtema para que el alumno estudie..."
    }},
    ...
  ]
}}

Contenido transcrito de los audios:
{contexto}
"""

    solicitud = Solicitud(
        id_usuario=usuario_id,
        tipo="PRESENTACION",
        prompt_usado=prompt[:1000],
        estado="PROCESANDO"
    )
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)
    
    for audio_id in audio_ids:
        rel = SolicitudAudio(id_solicitud=solicitud.id, id_audio=audio_id)
        db.add(rel)
    db.commit()
    
    try:
        json_data = None
        error_msg = ""
        
        try:
            res_text = generar_presentacion_con_ollama(prompt)
            json_data = limpiar_y_parsear_json(res_text)
        except Exception as ollama_err:
            ollama_desc = str(ollama_err)
            print(f"Ollama falló para generar presentación ({ollama_desc}). Intentando con Gemini...")
            try:
                res_text = generar_presentacion_con_gemini(prompt)
                json_data = limpiar_y_parsear_json(res_text)
            except Exception as gemini_err:
                gemini_desc = str(gemini_err)
                error_msg = f"Ollama no está disponible ({ollama_desc}) y el fallback de Gemini falló ({gemini_desc})"
                
        if not json_data or "diapositivas" not in json_data:
            raise Exception(error_msg or "El formato del JSON devuelto por la IA es incorrecto")
            
        # Valores iniciales de diseño por defecto (se guardan serializados en la columna ruta)
        diseno_defecto = {
            "tema": "sky",
            "fuente": "Inter",
            "colorFondo": "#e0f2fe",
            "colorTitulo": "#0369a1",
            "colorTexto": "#334155"
        }
        
        presentacion = Presentacion(
            id_solicitud=solicitud.id,
            titulo=titulo or f"Presentación del {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ruta=json.dumps(diseno_defecto),
            contenido=json_data["diapositivas"],
            cantidad_diapositivas=len(json_data["diapositivas"])
        )
        db.add(presentacion)
        db.commit()
        db.refresh(presentacion)
        
        solicitud.estado = "COMPLETADO"
        solicitud.completado_en = datetime.now(timezone.utc)
        db.commit()
        
        return obtener_presentacion_usuario(db, presentacion.id, usuario_id)
        
    except Exception as e:
        solicitud.estado = "ERROR"
        solicitud.mensaje_error = str(e)
        db.commit()
        
        err_msg = str(e)
        if "503" in err_msg or "UNAVAILABLE" in err_msg:
            raise HTTPException(
                status_code=503,
                detail="El servicio de IA de Gemini está experimentando alta demanda (Error 503) y el servicio local de Ollama no pudo completarse. Por favor, intenta de nuevo en unos segundos."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar la presentación: {err_msg}"
        )


def obtener_presentacion_usuario(db: Session, pres_id: int, usuario_id: int):
    pres = (
        db.query(Presentacion)
        .join(Solicitud, Presentacion.id_solicitud == Solicitud.id)
        .filter(Presentacion.id == pres_id, Solicitud.id_usuario == usuario_id)
        .first()
    )
    if not pres:
        raise HTTPException(status_code=404, detail="Presentación no encontrada")
        
    diseno = {}
    if pres.ruta:
        try:
            diseno = json.loads(pres.ruta)
        except Exception:
            pass
            
    return {
        "id": pres.id,
        "titulo": pres.titulo,
        "diseno": diseno,
        "contenido": pres.contenido,
        "cantidad_diapositivas": pres.cantidad_diapositivas,
        "creado_en": pres.creado_en.isoformat() if pres.creado_en else None
    }


def guardar_cambios_presentacion(
    db: Session,
    pres_id: int,
    usuario_id: int,
    titulo: str,
    contenido: list,
    diseno: dict
):
    pres = (
        db.query(Presentacion)
        .join(Solicitud, Presentacion.id_solicitud == Solicitud.id)
        .filter(Presentacion.id == pres_id, Solicitud.id_usuario == usuario_id)
        .first()
    )
    if not pres:
        raise HTTPException(status_code=404, detail="Presentación no encontrada")
        
    pres.titulo = titulo
    pres.contenido = contenido
    pres.ruta = json.dumps(diseno)
    pres.cantidad_diapositivas = len(contenido)
    
    db.commit()
    db.refresh(pres)
    
    return {
        "id": pres.id,
        "titulo": pres.titulo,
        "diseno": diseno,
        "contenido": pres.contenido,
        "cantidad_diapositivas": pres.cantidad_diapositivas
    }


def listar_historial_presentaciones(db: Session, usuario_id: int):
    presentaciones = (
        db.query(Presentacion)
        .join(Solicitud, Presentacion.id_solicitud == Solicitud.id)
        .filter(Solicitud.id_usuario == usuario_id)
        .order_by(Presentacion.creado_en.desc())
        .all()
    )
    
    historial = []
    for p in presentaciones:
        diseno = {}
        if p.ruta:
            try:
                diseno = json.loads(p.ruta)
            except Exception:
                pass
                
        historial.append({
            "id": p.id,
            "titulo": p.titulo,
            "cantidad_diapositivas": p.cantidad_diapositivas,
            "diseno": diseno,
            "creado_en": p.creado_en.isoformat() if p.creado_en else None
        })
        
    return historial
