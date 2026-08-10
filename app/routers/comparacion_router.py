from typing import Annotated

from fastapi import APIRouter, Depends

from app.constants.roles import (
    ADMIN,
    OPERADOR,
)
from app.schemas.user_schema import CurrentUser
from app.security.dependencies import require_role
from app.services.comparacion_service import (
    comparar_sistema_con_dbf,
)


router = APIRouter(
    prefix="/comparacion",
    tags=["Comparación"],
)


@router.post("/run")
def ejecutar_comparacion(
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
    return comparar_sistema_con_dbf(
        fecha=fecha,
        turno=turno,
    )