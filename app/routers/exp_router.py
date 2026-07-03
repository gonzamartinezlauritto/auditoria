import shutil
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.exp_service import process_exp, process_exp_fast
from app.services.zip_service import extraer_quiniela_exp_desde_zip

from app.config import UPLOADS_DIR

router = APIRouter(
    prefix="/exp",
    tags=["EXP"],
)


@router.get("/test")
def test_exp_router():
    return {"message": "Router EXP funcionando"}


@router.post("/upload")
async def upload_exp(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".exp"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe tener extensión .exp"
        )

    file_path = UPLOADS_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size_bytes = file_path.stat().st_size

    return {
        "message": "Archivo EXP subido correctamente",
        "filename": file.filename,
        "path": str(file_path),
        "size_bytes": size_bytes,
    }

@router.post("/process")
async def process_uploaded_exp(
    fecha: int,
    turno: str,
    file: UploadFile = File(...)
):
    start_total = time.time()

    file_path = UPLOADS_DIR / file.filename

    start_save = time.time()

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    save_seconds = time.time() - start_save

    size_bytes = file_path.stat().st_size

    start_process = time.time()

    resultado = process_exp_fast(
        file_path=file_path,
        fecha=fecha,
        turno=turno.upper()
    )

    process_seconds = time.time() - start_process

    total_seconds = time.time() - start_total

    resultado["archivo"] = {
        "filename": file.filename,
        "path": str(file_path),
        "size_bytes": size_bytes,
    }

    resultado["tiempos_router"] = {
        "guardar_archivo_segundos": round(save_seconds, 2),
        "procesar_exp_segundos": round(process_seconds, 2),
        "total_segundos": round(total_seconds, 2),
    }

    return resultado

@router.post("/process-zip")
async def process_exp_zip(
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

    extract_dir = UPLOADS_DIR / str(fecha) / turno / "exp"
    extract_dir.mkdir(parents=True, exist_ok=True)

    zip_path = extract_dir / file.filename

    with zip_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    exp_path = extraer_quiniela_exp_desde_zip(
        zip_path=zip_path,
        destino_dir=extract_dir
    )

    resultado = process_exp_fast(
        file_path=exp_path,
        fecha=fecha,
        turno=turno
    )

    resultado["zip"] = {
        "archivo_zip": file.filename,
        "path_zip": str(zip_path),
        "archivo_exp": exp_path.name,
        "path_exp": str(exp_path),
        "carpeta": str(extract_dir),
    }

    resultado["tiempo_total_zip"] = round(
        time.time() - start_total,
        2
    )

    return resultado
