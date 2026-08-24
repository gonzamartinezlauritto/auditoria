from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from app.constants.roles import (
    ADMIN,
    OPERADOR,
)
from app.docs.comparacion_docs import (
    RUN_COMPARACION_DOCS,
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


@router.post(
    "/run",
    **RUN_COMPARACION_DOCS,
)
def ejecutar_comparacion(
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
                "Turno a comparar. "
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
            )
        ),
    ],
):
    return comparar_sistema_con_dbf(
        fecha=fecha,
        turno=turno,
    )