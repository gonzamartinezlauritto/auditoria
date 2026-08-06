import shutil
from pathlib import Path

from fastapi import UploadFile

from app.exceptions.exp_exceptions import (
    ExtensionExpInvalidaError,
    ExtensionZipInvalidaError,
    NombreArchivoInvalidoError,
)
from app.exceptions.dbf_exceptions import (
    ExtensionDbfInvalidaError,
)

def validar_extension_dbf(
    nombre_archivo: str,
) -> None:
    if not nombre_archivo.lower().endswith(".dbf"):
        raise ExtensionDbfInvalidaError()

def obtener_nombre_seguro(
    file: UploadFile,
) -> str:
    if not file.filename:
        raise NombreArchivoInvalidoError()

    nombre_archivo = Path(file.filename).name

    if not nombre_archivo:
        raise NombreArchivoInvalidoError()

    return nombre_archivo


def validar_extension_exp(
    nombre_archivo: str,
) -> None:
    if not nombre_archivo.lower().endswith(".exp"):
        raise ExtensionExpInvalidaError()


def validar_extension_zip(
    nombre_archivo: str,
) -> None:
    if not nombre_archivo.lower().endswith(".zip"):
        raise ExtensionZipInvalidaError()


def guardar_upload(
    file: UploadFile,
    destino: Path,
) -> Path:
    destino.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with destino.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer,
        )

    return destino