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
from app.docs.auditoria_docs import (
    ESTADO_AUDITORIA_DOCS,
)
from app.schemas.user_schema import CurrentUser
from app.security.dependencies import require_role
from app.services.auditoria_estado_service import (
    obtener_estado_por_fecha,
)


router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría"],
)


@router.get(
    "/estado",
    **ESTADO_AUDITORIA_DOCS,
)
def estado_auditoria(
    fecha: Annotated[
        int,
        Query(
            gt=0,
            description="Fecha del sorteo en formato AAAAMMDD.",
            examples=[20260810],
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
    return obtener_estado_por_fecha(
        fecha=fecha,
    )