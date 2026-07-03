from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.exp_router import router as exp_router
from app.routers.dbf_router import router as dbf_router
from app.routers.calculo_router import router as calculo_router
from app.routers.resultados_router import router as resultados_router
from app.routers import auditoria_router

app = FastAPI(
    title="Auditoría Quiniela API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exp_router)
app.include_router(dbf_router)
app.include_router(calculo_router)
app.include_router(resultados_router)
app.include_router(auditoria_router.router)

@app.get("/")
def health():
    return {
        "message": "API Auditoría Quiniela funcionando"
    }