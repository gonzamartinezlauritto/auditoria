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
from app.docs.calculo_docs import (
    RESUMEN_CALCULO_DOCS,
    RUN_CALCULO_DOCS,
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


@router.post(
    "/run",
    **RUN_CALCULO_DOCS,
)
def run_calculo(
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
                "Turno a calcular. "
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
    return calcular_por_fecha_turno(
        fecha=fecha,
        turno=turno,
    )


@router.get(
    "/resumen",
    **RESUMEN_CALCULO_DOCS,
)
def resumen_por_fecha(
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
    return obtener_resumen_por_fecha(
        fecha=fecha,
    )