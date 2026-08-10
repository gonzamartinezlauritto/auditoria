from typing import Annotated

from fastapi import APIRouter, Depends

from app.constants.roles import (
    ADMIN,
    CONSULTA,
    OPERADOR,
)
from app.schemas.user_schema import CurrentUser
from app.security.dependencies import require_role
from app.services.calculo_service import (
    calcular_por_fecha_turno,
    obtener_resumen_por_fecha,
)


router = APIRouter(
    prefix="/calculo",
    tags=["Cálculo"],
)


@router.post("/run")
def run_calculo(
    fecha: int,
    turno: str,
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
    return calcular_por_fecha_turno(
        fecha=fecha,
        turno=turno,
    )


@router.get("/resumen")
def resumen_por_fecha(
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
    return obtener_resumen_por_fecha(
        fecha=fecha,
    )