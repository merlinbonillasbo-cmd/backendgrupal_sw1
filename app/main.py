from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import engine, Base
from app.routers.auth_router import auth_router
from app.routers.usuario_router import usuario_router
from app.routers.proyecto_router import proyecto_router
from app.routers.audio_router import audio_router
from app.routers.transcripcion_router import transcripcion_router
from app.routers.resumen_router import resumen_router
from app.routers.chat_router import chat_router
from app.routers.grafo_router import grafo_router
from app.routers.quiz_router import quiz_router
from app.routers.presentacion_router import presentacion_router


# Crea las tablas definidas en los modelos SQLAlchemy
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Software 1",
    version="1.0.0",
    description="Sistema inteligente para procesamiento y análisis de audios"
)


# URLs permitidas del frontend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)


# Routers
app.include_router(auth_router)
app.include_router(usuario_router)
app.include_router(proyecto_router)
app.include_router(audio_router)
app.include_router(transcripcion_router)
app.include_router(resumen_router)
app.include_router(chat_router)
app.include_router(grafo_router)
app.include_router(quiz_router)
app.include_router(presentacion_router)



@app.get("/")
def home():
    return {"mensaje": "FastAPI funcionando"}