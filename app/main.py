from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.db import engine, Base
from app.routers.user_router import user_router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Software 1")



# 1. Define las URLs de los frontends que tienen permitido acceder a tu API
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",  # Agrega este también por seguridad
]

# 2. Agrega el middleware de CORS a la aplicación
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Permite las peticiones desde los origins definidos
    allow_credentials=True,          # Permite el envío de cookies o cabeceras de autenticación
    allow_methods=["*"],             # Permite todos los métodos HTTP (GET, POST, PUT, DELETE, etc.)
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)



app.include_router(user_router, prefix="/api/usuario", tags=["Users"])


@app.get("/")
def home():
    return {"mensaje": "FastAPI funcionando"}


