from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from app.constants.roles import (
    ADMIN,
    CONSULTA,
    OPERADOR,
)
from app.docs.reporte_docs import (
    CONTROL_ACIERTOS_DOCS,
)
from app.schemas.user_schema import CurrentUser
from app.security.dependencies import require_role
from app.services.reporte_service import (
    obtener_control_aciertos,
)


router = APIRouter(
    prefix="/reporte",
    tags=["Reporte"],
)


@router.get(
    "/control-aciertos",
    **CONTROL_ACIERTOS_DOCS,
)
def control_aciertos(
    fecha: Annotated[
        int,
        Query(
            gt=0,
            description="Fecha del sorteo en formato AAAAMMDD.",
            examples=[20260810],
        ),
    ],
    turno: Annotated[
        str,
        Query(
            min_length=1,
            max_length=10,
            description=(
                "Turno correspondiente al reporte. "
                "Valores válidos: PV, PR, M, V o N."
            ),
            examples=["PV"],
        ),
    ],
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
    return obtener_control_aciertos(
        fecha=fecha,
        turno=turno,
    )