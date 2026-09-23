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
from app.docs.proceso_docs import (
    GET_ESTADO_PROCESO_DOCS,
)
from app.schemas.user_schema import CurrentUser
from app.security.dependencies import require_role
from app.services.proceso_service import (
    obtener_estado_proceso,
)


router = APIRouter(
    prefix="/proceso",
    tags=["Proceso de Quiniela"],
)


@router.get(
    "/estado",
    **GET_ESTADO_PROCESO_DOCS,
)
def consultar_estado_proceso(
    fecha: Annotated[
        int,
        Query(
            gt=0,
            description="Fecha del sorteo en formato AAAAMMDD.",
            examples=[20260910],
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
    return obtener_estado_proceso(
        fecha=fecha,
    )