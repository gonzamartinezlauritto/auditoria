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
    CERRAR_EVENTO_DOCS,
    ESTADO_AUDITORIA_DOCS,
    HISTORIAL_EVENTO_DOCS,
    REABRIR_EVENTO_DOCS,
)
from app.schemas.auditoria_schema import (
    ReabrirEventoRequest,
)
from app.schemas.user_schema import CurrentUser
from app.security.dependencies import require_role
from app.services.auditoria_estado_service import (
    cerrar_evento,
    obtener_estado_por_fecha,
    obtener_historial_evento,
    reabrir_evento,
)


router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría"],
)


# =========================================================
# ESTADO
# =========================================================

@router.get(
    "/estado",
    **ESTADO_AUDITORIA_DOCS,
)
def estado_auditoria(
    fecha: Annotated[
        int,
        Query(
            gt=0,
            description=(
                "Fecha del sorteo en formato AAAAMMDD."
            ),
            examples=[20260910],
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


# =========================================================
# CERRAR EVENTO
# =========================================================

@router.post(
    "/cerrar",
    **CERRAR_EVENTO_DOCS,
)
def cerrar_evento_auditoria(
    fecha: Annotated[
        int,
        Query(
            gt=0,
            description=(
                "Fecha del sorteo en formato AAAAMMDD."
            ),
            examples=[20260910],
        ),
    ],
    turno: Annotated[
        str,
        Query(
            min_length=1,
            max_length=10,
            description=(
                "Turno correspondiente al evento."
            ),
            examples=["PV"],
        ),
    ],
    usuario_actual: Annotated[
        CurrentUser,
        Depends(
            require_role(
                ADMIN,
                OPERADOR,
            )
        ),
    ],
):
    return cerrar_evento(
        fecha=fecha,
        turno=turno,
        usuario=usuario_actual.username,
    )


# =========================================================
# REABRIR EVENTO
# =========================================================

@router.post(
    "/reabrir",
    **REABRIR_EVENTO_DOCS,
)
def reabrir_evento_auditoria(
    body: ReabrirEventoRequest,
    fecha: Annotated[
        int,
        Query(
            gt=0,
            description=(
                "Fecha del sorteo en formato AAAAMMDD."
            ),
            examples=[20260910],
        ),
    ],
    turno: Annotated[
        str,
        Query(
            min_length=1,
            max_length=10,
            description=(
                "Turno correspondiente al evento."
            ),
            examples=["PV"],
        ),
    ],
    usuario_actual: Annotated[
        CurrentUser,
        Depends(
            require_role(
                ADMIN,
            )
        ),
    ],
):
    return reabrir_evento(
        fecha=fecha,
        turno=turno,
        usuario=usuario_actual.username,
        motivo=body.motivo,
    )


# =========================================================
# HISTORIAL
# =========================================================

@router.get(
    "/historial",
    **HISTORIAL_EVENTO_DOCS,
)
def historial_evento_auditoria(
    fecha: Annotated[
        int,
        Query(
            gt=0,
            description=(
                "Fecha del sorteo en formato AAAAMMDD."
            ),
            examples=[20260910],
        ),
    ],
    turno: Annotated[
        str,
        Query(
            min_length=1,
            max_length=10,
            description=(
                "Turno correspondiente al evento."
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
    return obtener_historial_evento(
        fecha=fecha,
        turno=turno,
    )