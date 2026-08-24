from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.docs.openapi_docs import (
    API_DESCRIPTION,
    OPENAPI_TAGS,
)
from app.exceptions.base import AppException
from app.exceptions.handlers import app_exception_handler
from app.routers.auditoria_router import router as auditoria_router
from app.routers.auth_router import router as auth_router
from app.routers.calculo_router import router as calculo_router
from app.routers.comparacion_router import router as comparacion_router
from app.routers.dbf_router import router as dbf_router
from app.routers.exp_router import router as exp_router
from app.routers.reporte_router import router as reporte_router
from app.routers.resultados_router import router as resultados_router
from app.routers.users_router import router as users_router
from app.services.bootstrap_service import crear_admin_inicial


@asynccontextmanager
async def lifespan(app: FastAPI):
    crear_admin_inicial()

    yield


app = FastAPI(
    title="Auditoría Quiniela API",
    description=API_DESCRIPTION,
    version="1.0.0",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(
    AppException,
    app_exception_handler,
)


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(exp_router)
app.include_router(resultados_router)
app.include_router(calculo_router)
app.include_router(dbf_router)
app.include_router(comparacion_router)
app.include_router(auditoria_router)
app.include_router(reporte_router)


@app.get(
    "/",
    tags=["Sistema"],
    summary="Información de la API",
)
def root():
    return {
        "message": "API Auditoría Quiniela funcionando",
        "version": "1.0.0",
    }


@app.get(
    "/health",
    tags=["Sistema"],
    summary="Verificar estado de la API",
)
def health_check():
    return {
        "ok": True,
        "status": "healthy",
    }