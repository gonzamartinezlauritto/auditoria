from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    UploadFile,
)

from app.constants.roles import (
    ADMIN,
    OPERADOR,
)
from app.docs.dbf_docs import (
    PROCESS_DBF_DOCS,
    PROCESS_DBF_ZIP_DOCS,
)
from app.schemas.user_schema import CurrentUser
from app.security.dependencies import require_role
from app.services.dbf_service import (
    procesar_archivo_dbf,
    procesar_archivo_dbf_zip,
)


router = APIRouter(
    prefix="/dbf",
    tags=["DBF"],
)


@router.post(
    "/process",
    **PROCESS_DBF_DOCS,
)
def process_uploaded_dbf(
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
                "Turno correspondiente al DBF. "
                "Valores válidos: PV, PR, M, V o N."
            ),
            examples=["PV"],
        ),
    ],
    file: Annotated[
        UploadFile,
        File(
            ...,
            description=(
                "Archivo .dbf que contiene los "
                "aciertos oficiales."
            ),
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
    return procesar_archivo_dbf(
        file=file,
        fecha=fecha,
        turno=turno,
    )


@router.post(
    "/process-zip",
    **PROCESS_DBF_ZIP_DOCS,
)
def process_dbf_zip(
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
                "Turno correspondiente al DBF. "
                "Valores válidos: PV, PR, M, V o N."
            ),
            examples=["PV"],
        ),
    ],
    file: Annotated[
        UploadFile,
        File(
            ...,
            description=(
                "Archivo ZIP que contiene "
                "el archivo DBF de aciertos."
            ),
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
    return procesar_archivo_dbf_zip(
        file=file,
        fecha=fecha,
        turno=turno,
    )