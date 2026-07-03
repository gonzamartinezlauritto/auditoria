import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
import time

from app.config import UPLOADS_DIR
from app.services.dbf_service import process_dbf
from app.services.zip_service import extraer_dbf_desde_zip


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


@router.post("/process-zip")
async def process_dbf_zip(
    fecha: int,
    turno: str,
    file: UploadFile = File(...)
):
    start_total = time.time()

    turno = turno.upper().strip()

    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser ZIP"
        )

    extract_dir = UPLOADS_DIR / str(fecha) / turno / "dbf"
    extract_dir.mkdir(parents=True, exist_ok=True)

    zip_path = extract_dir / file.filename

    with zip_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    dbf_path = extraer_dbf_desde_zip(
        zip_path=zip_path,
        destino_dir=extract_dir
    )

    resultado = process_dbf(
        file_path=dbf_path,
        fecha=fecha,
        turno=turno
    )

    resultado["zip"] = {
        "archivo_zip": file.filename,
        "path_zip": str(zip_path),
        "archivo_dbf": dbf_path.name,
        "path_dbf": str(dbf_path),
        "carpeta": str(extract_dir),
    }

    resultado["tiempo_total_zip"] = round(
        time.time() - start_total,
        2
    )

    return resultado