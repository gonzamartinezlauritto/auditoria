import shutil

from fastapi import APIRouter, UploadFile, File

from app.config import UPLOADS_DIR
from app.services.dbf_service import process_dbf

router = APIRouter(
    prefix="/dbf",
    tags=["DBF"]
)


@router.post("/process")
async def process_uploaded_dbf(
    fecha: int,
    turno: str,
    file: UploadFile = File(...)
):
    file_path = UPLOADS_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    resultado = process_dbf(
        file_path=file_path,
        fecha=fecha,
        turno=turno.upper()
    )

    return resultado