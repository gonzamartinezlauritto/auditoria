import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.exp_service import process_exp, process_exp_fast

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
    file_path = UPLOADS_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    resultado = process_exp_fast(
        file_path=file_path,
        fecha=fecha,
        turno=turno.upper()
    )

    return resultado