from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Query,
)

from app.constants.roles import (
    ADMIN,
    CONSULTA,
    OPERADOR,
)
from app.docs.extractos_docs import (
    CARGAR_EXTRACTOS_DOCS,
    CARGAR_EXTRACTOS_EXAMPLES,
    CONSULTAR_EXTRACTOS_DOCS,
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
    prefix="/extractos",
    tags=["Extractos"],
)


@router.post(
    "/cargar",
    **CARGAR_EXTRACTOS_DOCS,
)
def cargar_resultados_endpoint(
    body: Annotated[
        CargarResultadosRequest,
        Body(
            openapi_examples=CARGAR_EXTRACTOS_EXAMPLES,
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
    resultados = [
        item.model_dump()
        for item in body.resultados
    ]

    return cargar_resultados(
        fecha=body.fecha,
        turno=body.turno,
        resultados=resultados,
    )


@router.get(
    "",
    **CONSULTAR_EXTRACTOS_DOCS,
)
def listar_resultados(
    fecha: Annotated[
        int,
        Query(
            gt=0,
            description=(
                "Fecha del sorteo en formato AAAAMMDD."
            ),
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
    return obtener_resultados_por_fecha(
        fecha=fecha,
    )