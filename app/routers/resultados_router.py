from typing import List
from pydantic import BaseModel
from fastapi import APIRouter

from app.services.resultados_service import cargar_resultados


class ResultadoExtractoRequest(BaseModel):
    codigo_extracto: int
    numeros: List[str]


class CargarResultadosRequest(BaseModel):
    fecha: int
    turno: str
    resultados: List[ResultadoExtractoRequest]


router = APIRouter(
    prefix="/resultados",
    tags=["Resultados"],
)


@router.post("/cargar")
def cargar_resultados_endpoint(body: CargarResultadosRequest):
    resultados = [
        item.model_dump()
        for item in body.resultados
    ]

    return cargar_resultados(
        fecha=body.fecha,
        turno=body.turno,
        resultados=resultados,
    )