from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
import time

from dbfread import DBF
from fastapi import UploadFile

from app.config import UPLOADS_DIR
from app.core.logger import logger
from app.core.transaction import transaction
from app.exceptions.base import AppException
from app.exceptions.dbf_exceptions import (
    ArchivoDbfInvalidoError,
    ErrorProcesamientoDbf,
)
from app.repositories import dbf_repository
from app.services.auditoria_estado_service import (
    marcar_dbf_cargado,
)
from app.services.file_service import (
    guardar_upload,
    obtener_nombre_seguro,
    validar_extension_dbf,
    validar_extension_zip,
)
from app.services.zip_service import extraer_dbf_desde_zip


def _to_int(
    value: Any,
) -> int | None:
    if value in (None, ""):
        return None

    try:
        return int(value)

    except (TypeError, ValueError):
        return None


def _to_decimal(
    value: Any,
) -> Decimal:
    if value in (None, ""):
        return Decimal("0.00")

    try:
        return Decimal(str(value))

    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


def procesar_archivo_dbf(
    file: UploadFile,
    fecha: int,
    turno: str,
) -> dict[str, Any]:
    inicio_total = time.perf_counter()

    nombre_archivo = obtener_nombre_seguro(file)
    validar_extension_dbf(nombre_archivo)

    turno_normalizado = turno.upper().strip()

    file_path = guardar_upload(
        file=file,
        destino=UPLOADS_DIR / nombre_archivo,
    )

    resultado = process_dbf(
        file_path=file_path,
        fecha=fecha,
        turno=turno_normalizado,
    )

    resultado["archivo"] = {
        "filename": nombre_archivo,
        "path": str(file_path),
        "size_bytes": file_path.stat().st_size,
    }

    resultado["tiempo_total_segundos"] = round(
        time.perf_counter() - inicio_total,
        2,
    )

    return resultado


def procesar_archivo_dbf_zip(
    file: UploadFile,
    fecha: int,
    turno: str,
) -> dict[str, Any]:
    inicio_total = time.perf_counter()

    nombre_archivo = obtener_nombre_seguro(file)
    validar_extension_zip(nombre_archivo)

    turno_normalizado = turno.upper().strip()

    extract_dir = (
        UPLOADS_DIR
        / str(fecha)
        / turno_normalizado
        / "dbf"
    )

    zip_path = guardar_upload(
        file=file,
        destino=extract_dir / nombre_archivo,
    )

    dbf_path = extraer_dbf_desde_zip(
        zip_path=zip_path,
        destino_dir=extract_dir,
    )

    resultado = process_dbf(
        file_path=dbf_path,
        fecha=fecha,
        turno=turno_normalizado,
    )

    resultado["zip"] = {
        "archivo_zip": nombre_archivo,
        "path_zip": str(zip_path),
        "archivo_dbf": dbf_path.name,
        "path_dbf": str(dbf_path),
        "carpeta": str(extract_dir),
    }

    resultado["tiempo_total_zip"] = round(
        time.perf_counter() - inicio_total,
        2,
    )

    return resultado


def process_dbf(
    file_path: Path,
    fecha: int,
    turno: str,
) -> dict[str, Any]:
    turno_normalizado = turno.upper().strip()
    inicio_total = time.perf_counter()

    try:
        try:
            tabla = DBF(
                file_path,
                encoding="latin1",
            )

        except Exception as error:
            raise ArchivoDbfInvalidoError() from error

        with transaction() as conn:
            dbf_repository.eliminar_aciertos_por_fecha_turno(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
            )

            insertados = 0

            for row in tabla:
                dbf_repository.insertar_acierto(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                    codigo_extracto=_to_int(
                        row.get("EXTRACTO")
                    ),
                    agencia=_to_int(
                        row.get("AGENCIA")
                    ),
                    subagencia=_to_int(
                        row.get("SUBAGENCIA")
                    ),
                    nromaquina=_to_int(
                        row.get("NROMAQUINA")
                    ),
                    numero=_to_int(
                        row.get("NUMERO")
                    ),
                    apuestas=_to_int(
                        row.get("APUESTAS")
                    ),
                    ap_acierto=_to_int(
                        row.get("AP_ACIERTO")
                    ),
                    apostado=_to_decimal(
                        row.get("APOSTADO")
                    ),
                    impganado=_to_decimal(
                        row.get("IMPGANADO")
                    ),
                )

                insertados += 1

            resumen_extractos = (
                dbf_repository.obtener_resumen_extractos(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            cupones_unicos = (
                dbf_repository.contar_cupones_ganadores_unicos(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            marcar_dbf_cargado(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
                archivo_dbf=file_path.name,
            )

        tiempo_total = round(
            time.perf_counter() - inicio_total,
            2,
        )

        logger.info(
            "Archivo DBF procesado: "
            "archivo=%s fecha=%s turno=%s "
            "filas_insertadas=%s cupones_unicos=%s",
            file_path.name,
            fecha,
            turno_normalizado,
            insertados,
            cupones_unicos,
        )

        return {
            "ok": True,
            "archivo_origen": file_path.name,
            "fecha": fecha,
            "turno": turno_normalizado,
            "filas_insertadas": insertados,
            "extractos": resumen_extractos,
            "cupones_ganadores_unicos": cupones_unicos,
            "tiempos_service": {
                "total_segundos": tiempo_total,
            },
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error al procesar archivo DBF: "
            "archivo=%s fecha=%s turno=%s",
            file_path.name,
            fecha,
            turno_normalizado,
        )

        raise ErrorProcesamientoDbf(
            "Error al procesar el archivo DBF"
        ) from error