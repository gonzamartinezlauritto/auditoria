from fastapi import APIRouter
from app.services.auditoria_estado_service import obtener_estado_por_fecha

router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría"],
)


@router.get("/estado")
def estado_auditoria(fecha: int):
    return obtener_estado_por_fecha(fecha)