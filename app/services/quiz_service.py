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
from app.models.quiz import Quiz, PreguntaQuiz
from app.models.audio import Audio


def listar_audios_disponibles(db: Session, usuario_id: int):
    """
    Lista todos los audios del usuario que están listos y transcritos
    para poder ser seleccionados en la generación del quiz.
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
    """
    Intenta conectarse al puerto 11434 de ollama en docker, localhost y 127.0.0.1
    para encontrar la dirección activa.
    """
    for host in ["ollama", "localhost", "127.0.0.1"]:
        try:
            url = f"http://{host}:11434/api/tags"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return f"http://{host}:11434"
        except Exception:
            continue
    return "http://ollama:11434"  # Default fallback


def seleccionar_modelo_ollama(active_url: str) -> str:
    """
    Detecta automáticamente qué modelo generativo de texto está descargado en Ollama.
    """
    try:
        url = f"{active_url}/api/tags"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            names = [m["name"] for m in models]
            # Excluir modelos de embedding
            generativos = [n for n in names if "embed" not in n]
            if generativos:
                # Priorizar modelos comunes
                for fav in ["llama3.2", "llama3", "mistral", "gemma", "phi3"]:
                    for g in generativos:
                        if fav in g:
                            return g
                return generativos[0]
    except Exception:
        pass
    return "llama3.2"  # Default fallbackdocker compose down && docker compose up -d



def generar_quiz_con_ollama(prompt: str) -> str:
    active_url = obtener_url_ollama_activa()
    model = seleccionar_modelo_ollama(active_url)
    
    url = f"{active_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        # Omitimos format: json temporalmente por si la versión instalada de Ollama no lo soporta.
    }
    response = requests.post(url, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()["response"].strip()


def generar_quiz_con_gemini(prompt: str) -> str:
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


def crear_quiz_estudio(
    db: Session,
    usuario_id: int,
    titulo: str,
    audio_ids: list[int]
) -> Quiz:
    if not audio_ids:
        raise HTTPException(
            status_code=400,
            detail="Debes seleccionar al menos un audio para generar el quiz"
        )
        
    # 1. Obtener los textos de transcripción y validar pertenencia
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
    
    # 2. Construir el prompt de RAG
    prompt = f"""
Eres un profesor universitario experto. Basándote ÚNICAMENTE en el siguiente contenido transcrito de los audios del estudiante, genera un cuestionario (quiz) de 5 preguntas de opción múltiple para ayudarle a estudiar.

Reglas obligatorias:
1. El cuestionario debe constar exactamente de 5 preguntas de opción múltiple.
2. Cada pregunta debe tener exactamente 4 opciones de respuesta (con las letras A, B, C, D).
3. Debe haber una única opción correcta para cada pregunta.
4. Genera una explicación breve de por qué esa opción es correcta.
5. Usa el mismo idioma del contenido transcrito (Español).
6. Responde ÚNICAMENTE con un objeto JSON válido, sin textos introductorios, sin bloques de código tipo ```json, ni explicaciones externas.

Formato del JSON de respuesta:
{{
  "preguntas": [
    {{
      "pregunta": "¿Texto de la pregunta 1?",
      "opciones": [
        "Opción A",
        "Opción B",
        "Opción C",
        "Opción D"
      ],
      "correcta": "Letra de la opción correcta (A, B, C o D)",
      "explicacion": "Explicación detallada de la respuesta correcta"
    }},
    ...
  ]
}}

Contenido transcrito:
{contexto}
"""

    # 3. Crear registro de Solicitud en la base de datos
    solicitud = Solicitud(
        id_usuario=usuario_id,
        tipo="QUIZ",
        prompt_usado=prompt[:1000],  # Guardamos parte del prompt por registro
        estado="PROCESANDO"
    )
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)
    
    # Vincular audios a la solicitud
    for audio_id in audio_ids:
        rel = SolicitudAudio(id_solicitud=solicitud.id, id_audio=audio_id)
        db.add(rel)
    db.commit()
    
    # 4. Generar el Quiz con IA (Ollama con fallback a Gemini)
    try:
        json_data = None
        error_msg = ""
        
        try:
            res_text = generar_quiz_con_ollama(prompt)
            json_data = limpiar_y_parsear_json(res_text)
        except Exception as ollama_err:
            ollama_desc = str(ollama_err)
            print(f"Ollama falló para generar quiz ({ollama_desc}). Intentando con Gemini...")
            try:
                res_text = generar_quiz_con_gemini(prompt)
                json_data = limpiar_y_parsear_json(res_text)
            except Exception as gemini_err:
                gemini_desc = str(gemini_err)
                error_msg = f"Ollama no está disponible ({ollama_desc}) y el fallback de Gemini falló ({gemini_desc})"
                
        if not json_data or "preguntas" not in json_data:
            raise Exception(error_msg or "El formato del JSON devuelto por la IA es incorrecto")
            
        # 5. Crear el Quiz y Preguntas en la BD
        quiz = Quiz(
            id_solicitud=solicitud.id,
            titulo=titulo or f"Quiz del {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            total_preguntas=len(json_data["preguntas"]),
            url_archivo=json.dumps({"completado": False})
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        for idx, q in enumerate(json_data["preguntas"], start=1):
            pregunta = PreguntaQuiz(
                id_quizzes=quiz.id,
                indice_pregunta=idx,
                texto_pregunta=json.dumps({
                    "pregunta": q["pregunta"],
                    "opciones": q["opciones"]
                }),
                texto_respuesta=json.dumps({
                    "correcta": q["correcta"].upper().strip(),
                    "explicacion": q["explicacion"]
                })
            )
            db.add(pregunta)
            
        # Actualizar solicitud
        solicitud.estado = "COMPLETADO"
        solicitud.completado_en = datetime.now(timezone.utc)
        db.commit()
        
        return quiz
        
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
            detail=f"Error al generar el Quiz: {err_msg}"
        )


def obtener_quiz_usuario(db: Session, quiz_id: int, usuario_id: int):
    """
    Retorna los datos de un Quiz específico del usuario, formateando
    las preguntas de vuelta a objetos legibles.
    """
    quiz = (
        db.query(Quiz)
        .join(Solicitud, Quiz.id_solicitud == Solicitud.id)
        .filter(Quiz.id == quiz_id, Solicitud.id_usuario == usuario_id)
        .first()
    )
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz no encontrado")
        
    preguntas_db = (
        db.query(PreguntaQuiz)
        .filter(PreguntaQuiz.id_quizzes == quiz_id)
        .order_by(PreguntaQuiz.indice_pregunta.asc())
        .all()
    )
    
    preguntas_formateadas = []
    for p in preguntas_db:
        try:
            preg_info = json.loads(p.texto_pregunta)
            resp_info = json.loads(p.texto_respuesta)
            preguntas_formateadas.append({
                "id": p.id,
                "indice": p.indice_pregunta,
                "pregunta": preg_info.get("pregunta"),
                "opciones": preg_info.get("opciones"),
                "correcta": resp_info.get("correcta"),
                "explicacion": resp_info.get("explicacion")
            })
        except Exception:
            preguntas_formateadas.append({
                "id": p.id,
                "indice": p.indice_pregunta,
                "pregunta": p.texto_pregunta,
                "opciones": [],
                "correcta": p.texto_respuesta,
                "explicacion": ""
            })
            
    # Intentar parsear el estado/calificación
    resultado_info = {"completado": False}
    if quiz.url_archivo:
        try:
            resultado_info = json.loads(quiz.url_archivo)
        except Exception:
            pass
            
    return {
        "id": quiz.id,
        "titulo": quiz.titulo,
        "total_preguntas": quiz.total_preguntas,
        "creado_en": quiz.creado_en.isoformat() if quiz.creado_en else None,
        "resultado": resultado_info,
        "preguntas": preguntas_formateadas
    }


def guardar_resultado_quiz(
    db: Session,
    quiz_id: int,
    usuario_id: int,
    bien: int,
    mal: int,
    respuestas_usuario: list[str]
):
    """
    Registra el puntaje y las respuestas del usuario para un Quiz.
    """
    quiz = (
        db.query(Quiz)
        .join(Solicitud, Quiz.id_solicitud == Solicitud.id)
        .filter(Quiz.id == quiz_id, Solicitud.id_usuario == usuario_id)
        .first()
    )
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz no encontrado")
        
    resultado_json = {
        "completado": True,
        "bien": bien,
        "mal": mal,
        "respuestas_usuario": respuestas_usuario,
        "fecha_resolucion": datetime.now(timezone.utc).isoformat()
    }
    
    quiz.url_archivo = json.dumps(resultado_json)
    db.commit()
    db.refresh(quiz)
    
    return resultado_json


def listar_historial_quizzes(db: Session, usuario_id: int):
    """
    Retorna la lista de quizzes generados por el usuario con sus resultados.
    """
    quizzes = (
        db.query(Quiz)
        .join(Solicitud, Quiz.id_solicitud == Solicitud.id)
        .filter(Solicitud.id_usuario == usuario_id)
        .order_by(Quiz.creado_en.desc())
        .all()
    )
    
    historial = []
    for q in quizzes:
        resultado_info = {"completado": False}
        if q.url_archivo:
            try:
                resultado_info = json.loads(q.url_archivo)
            except Exception:
                pass
                
        historial.append({
            "id": q.id,
            "titulo": q.titulo,
            "total_preguntas": q.total_preguntas,
            "creado_en": q.creado_en.isoformat() if q.creado_en else None,
            "resultado": resultado_info
        })
        
    return historial
