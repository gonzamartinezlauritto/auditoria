from typing import Annotated

from fastapi import APIRouter, Depends

from app.constants.roles import (
    ADMIN,
    CONSULTA,
    OPERADOR,
)
from app.schemas.resultados_schema import (
    CargarResultadosRequest,
)
from app.schemas.user_schema import CurrentUser
from app.security.dependencies import require_role
from app.services.resultados_service import (
    cargar_resultados,
    obtener_resultados_por_fecha,
)


router = APIRouter(
    prefix="/resultados",
    tags=["Resultados"],
)


@router.post("/cargar")
def cargar_resultados_endpoint(
    body: CargarResultadosRequest,
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(
            require_role(
                ADMIN,
                OPERADOR,
            )
        ),
    ],
):
    resultados = [
        item.model_dump()
        for item in body.resultados
    ]

    return cargar_resultados(
        fecha=body.fecha,
        turno=body.turno,
        resultados=resultados,
    )


@router.get("")
def listar_resultados(
    fecha: int,
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(
            require_role(
                ADMIN,
                OPERADOR,
                CONSULTA,
            )
        ),
    ],
):
    return obtener_resultados_por_fecha(
        fecha=fecha,
    )