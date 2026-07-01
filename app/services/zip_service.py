from pathlib import Path
import zipfile
import io


def extraer_quiniela_exp_desde_zip(zip_path: Path, destino_dir: Path) -> Path:
    destino_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_externo:
        for nombre_externo in zip_externo.namelist():

            if nombre_externo.lower().endswith(".zip"):
                zip_interno_bytes = zip_externo.read(nombre_externo)

                with zipfile.ZipFile(io.BytesIO(zip_interno_bytes), "r") as zip_interno:
                    for nombre_interno in zip_interno.namelist():

                        if nombre_interno.lower().endswith("quiniela.exp"):
                            salida = destino_dir / "quiniela.exp"

                            with salida.open("wb") as f:
                                f.write(zip_interno.read(nombre_interno))

                            return salida

    raise Exception("No se encontró quiniela.exp dentro del ZIP")

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

