from pathlib import Path
import zipfile
import io
from zipfile import BadZipFile, ZipFile
from app.exceptions.exp_exceptions import (
    ArchivoExpNoEncontradoError,
    ArchivoZipInvalidoError,
)


from io import BytesIO
from pathlib import Path
import zipfile
from zipfile import BadZipFile, ZipFile

from app.exceptions.exp_exceptions import (
    ArchivoExpNoEncontradoError,
    ArchivoZipInvalidoError,
)


def _seleccionar_archivo_exp(
    archivo_zip: ZipFile,
):
    archivos_exp = [
        item
        for item in archivo_zip.infolist()
        if (
            not item.is_dir()
            and Path(item.filename).suffix.lower() == ".exp"
        )
    ]

    if not archivos_exp:
        return None

    return next(
        (
            item
            for item in archivos_exp
            if Path(item.filename).name.lower() == "quiniela.exp"
        ),
        archivos_exp[0],
    )


def _guardar_archivo_exp(
    archivo_zip: ZipFile,
    archivo_exp,
    destino_dir: Path,
) -> Path:
    nombre_salida = Path(archivo_exp.filename).name

    if not nombre_salida:
        raise ArchivoExpNoEncontradoError()

    exp_path = destino_dir / nombre_salida

    with archivo_zip.open(archivo_exp, "r") as origen:
        with exp_path.open("wb") as destino:
            while bloque := origen.read(1024 * 1024):
                destino.write(bloque)

    return exp_path


def extraer_quiniela_exp_desde_zip(
    zip_path: Path,
    destino_dir: Path,
) -> Path:
    destino_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with ZipFile(zip_path, "r") as archivo_zip:
            # Caso 1: el EXP está directamente en el ZIP principal.
            archivo_exp = _seleccionar_archivo_exp(
                archivo_zip,
            )

            if archivo_exp:
                return _guardar_archivo_exp(
                    archivo_zip=archivo_zip,
                    archivo_exp=archivo_exp,
                    destino_dir=destino_dir,
                )

            # Caso 2: el EXP está dentro de un ZIP anidado.
            archivos_zip_internos = [
                item
                for item in archivo_zip.infolist()
                if (
                    not item.is_dir()
                    and Path(item.filename).suffix.lower() == ".zip"
                )
            ]

            for zip_interno in archivos_zip_internos:
                contenido_zip = archivo_zip.read(
                    zip_interno,
                )

                try:
                    with ZipFile(
                        BytesIO(contenido_zip),
                        "r",
                    ) as archivo_zip_interno:
                        archivo_exp = _seleccionar_archivo_exp(
                            archivo_zip_interno,
                        )

                        if archivo_exp:
                            return _guardar_archivo_exp(
                                archivo_zip=archivo_zip_interno,
                                archivo_exp=archivo_exp,
                                destino_dir=destino_dir,
                            )

                except BadZipFile:
                    # Si uno de los archivos .zip internos está dañado,
                    # seguimos buscando en los demás.
                    continue

            raise ArchivoExpNoEncontradoError(
                "No se encontró quiniela.exp ni otro archivo .exp "
                "en el ZIP principal ni en sus ZIP internos"
            )

    except BadZipFile as error:
        raise ArchivoZipInvalidoError() from error


def extraer_dbf_desde_zip(zip_path: Path, destino_dir: Path) -> Path:
    destino_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as z:
        for nombre in z.namelist():
            if nombre.lower().endswith(".dbf"):
                salida = destino_dir / Path(nombre).name

                with salida.open("wb") as f:
                    f.write(z.read(nombre))

                return salida

    raise Exception("No se encontró archivo .dbf dentro del ZIP")

