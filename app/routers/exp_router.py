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
from app.docs.exp_docs import (
    PROCESS_EXP_DOCS,
    PROCESS_EXP_ZIP_DOCS,
    TEST_EXP_DOCS,
    UPLOAD_EXP_DOCS,
)
from app.schemas.user_schema import CurrentUser
from app.security.dependencies import require_role
from app.services.exp_service import (
    procesar_archivo_exp,
    procesar_archivo_exp_zip,
    subir_archivo_exp,
)


router = APIRouter(
    prefix="/exp",
    tags=["EXP"],
)


@router.get(
    "/test",
    **TEST_EXP_DOCS,
)
def test_exp_router(
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
    return {
        "message": "Router EXP funcionando",
    }


@router.post(
    "/upload",
    **UPLOAD_EXP_DOCS,
)
def upload_exp(
    file: Annotated[
        UploadFile,
        File(
            ...,
            description=(
                "Archivo EXP que se desea almacenar."
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
    return subir_archivo_exp(
        file=file,
    )


@router.post(
    "/process",
    **PROCESS_EXP_DOCS,
)
def process_uploaded_exp(
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
                "Turno a procesar. "
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
                "Archivo .exp que contiene las apuestas."
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
    return procesar_archivo_exp(
        file=file,
        fecha=fecha,
        turno=turno,
    )


@router.post(
    "/process-zip",
    **PROCESS_EXP_ZIP_DOCS,
)
def process_exp_zip(
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
                "Turno a procesar. "
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
                "Archivo ZIP que contiene el archivo EXP."
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
    return procesar_archivo_exp_zip(
        file=file,
        fecha=fecha,
        turno=turno,
    )