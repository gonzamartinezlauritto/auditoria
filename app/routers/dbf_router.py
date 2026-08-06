from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)

from app.constants.roles import ADMIN, OPERADOR
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


@router.post("/process")
def process_uploaded_dbf(
    fecha: int,
    turno: str,
    file: Annotated[
        UploadFile,
        File(...),
    ],
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN, OPERADOR)),
    ],
):
    return procesar_archivo_dbf(
        file=file,
        fecha=fecha,
        turno=turno,
    )


@router.post("/process-zip")
def process_dbf_zip(
    fecha: int,
    turno: str,
    file: Annotated[
        UploadFile,
        File(...),
    ],
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN, OPERADOR)),
    ],
):
    return procesar_archivo_dbf_zip(
        file=file,
        fecha=fecha,
        turno=turno,
    )