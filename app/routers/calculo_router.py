from fastapi import APIRouter

from app.services.calculo_service import calcular_por_fecha_turno

router = APIRouter(
    prefix="/calculo",
    tags=["Cálculo"],
)


@router.post("/run")
def run_calculo(fecha: int, turno: str):
    return calcular_por_fecha_turno(
        fecha=fecha,
        turno=turno.upper(),
    )