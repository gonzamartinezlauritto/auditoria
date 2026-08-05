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
from app.services.exp_service import (
    procesar_archivo_exp,
    procesar_archivo_exp_zip,
    subir_archivo_exp,
)


router = APIRouter(
    prefix="/exp",
    tags=["EXP"],
)


@router.get("/test")
def test_exp_router(
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN, OPERADOR)),
    ],
):
    return {
        "message": "Router EXP funcionando",
    }


@router.post("/upload")
def upload_exp(
    file: Annotated[
        UploadFile,
        File(...),
    ],
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN, OPERADOR)),
    ],
):
    return subir_archivo_exp(
        file=file,
    )


@router.post("/process")
def process_uploaded_exp(
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
    return procesar_archivo_exp(
        file=file,
        fecha=fecha,
        turno=turno,
    )


@router.post("/process-zip")
def process_exp_zip(
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
    return procesar_archivo_exp_zip(
        file=file,
        fecha=fecha,
        turno=turno,
    )