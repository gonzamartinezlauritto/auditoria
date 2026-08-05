from pathlib import Path
from typing import Any
import time

from fastapi import UploadFile

from app.config import UPLOADS_DIR
from app.core.logger import logger
from app.core.transaction import transaction
from app.exceptions.base import AppException
from app.exceptions.exp_exceptions import (
    ErrorProcesamientoExp,
    SinApuestasParaTurnoError,
)
from app.repositories import exp_repository
from app.services.auditoria_estado_service import marcar_exp_cargado
from app.services.file_service import (
    guardar_upload,
    obtener_nombre_seguro,
    validar_extension_exp,
    validar_extension_zip,
)
from app.services.zip_service import (
    extraer_quiniela_exp_desde_zip,
)


def subir_archivo_exp(
    file: UploadFile,
) -> dict[str, Any]:
    nombre_archivo = obtener_nombre_seguro(file)
    validar_extension_exp(nombre_archivo)

    file_path = guardar_upload(
        file=file,
        destino=UPLOADS_DIR / nombre_archivo,
    )

    return {
        "message": "Archivo EXP subido correctamente",
        "filename": nombre_archivo,
        "path": str(file_path),
        "size_bytes": file_path.stat().st_size,
    }


def procesar_archivo_exp(
    file: UploadFile,
    fecha: int,
    turno: str,
) -> dict[str, Any]:
    inicio_total = time.perf_counter()

    nombre_archivo = obtener_nombre_seguro(file)
    validar_extension_exp(nombre_archivo)

    turno_normalizado = turno.upper().strip()

    inicio_guardado = time.perf_counter()

    file_path = guardar_upload(
        file=file,
        destino=UPLOADS_DIR / nombre_archivo,
    )

    tiempo_guardado = (
        time.perf_counter() - inicio_guardado
    )

    inicio_procesamiento = time.perf_counter()

    resultado = process_exp_fast(
        file_path=file_path,
        fecha=fecha,
        turno=turno_normalizado,
    )

    tiempo_procesamiento = (
        time.perf_counter() - inicio_procesamiento
    )

    resultado["archivo"] = {
        "filename": nombre_archivo,
        "path": str(file_path),
        "size_bytes": file_path.stat().st_size,
    }

    resultado["tiempos_orquestacion"] = {
        "guardar_archivo_segundos": round(
            tiempo_guardado,
            2,
        ),
        "procesar_exp_segundos": round(
            tiempo_procesamiento,
            2,
        ),
        "total_segundos": round(
            time.perf_counter() - inicio_total,
            2,
        ),
    }

    return resultado


def procesar_archivo_exp_zip(
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
        / "exp"
    )

    zip_path = guardar_upload(
        file=file,
        destino=extract_dir / nombre_archivo,
    )

    exp_path = extraer_quiniela_exp_desde_zip(
        zip_path=zip_path,
        destino_dir=extract_dir,
    )

    resultado = process_exp_fast(
        file_path=exp_path,
        fecha=fecha,
        turno=turno_normalizado,
    )

    resultado["zip"] = {
        "archivo_zip": nombre_archivo,
        "path_zip": str(zip_path),
        "archivo_exp": exp_path.name,
        "path_exp": str(exp_path),
        "carpeta": str(extract_dir),
    }

    resultado["tiempo_total_zip"] = round(
        time.perf_counter() - inicio_total,
        2,
    )

    return resultado


def process_exp_fast(
    file_path: Path,
    fecha: int,
    turno: str,
) -> dict[str, Any]:
    archivo_origen = file_path.name
    turno_normalizado = turno.upper().strip()

    tiempos: dict[str, float] = {}
    total_inicio = time.perf_counter()

    try:
        with transaction() as conn:
            inicio = time.perf_counter()

            exp_repository.crear_tabla_temporal(
                conn=conn,
            )

            tiempos["crear_tmp_segundos"] = round(
                time.perf_counter() - inicio,
                2,
            )

            inicio = time.perf_counter()

            exp_repository.copiar_archivo_a_temporal(
                conn=conn,
                file_path=file_path,
            )

            tiempos["copy_tmp_segundos"] = round(
                time.perf_counter() - inicio,
                2,
            )

            inicio = time.perf_counter()

            total_archivo = (
                exp_repository.contar_total_temporal(
                    conn=conn,
                )
            )

            total_turnos_validos = (
                exp_repository.contar_turnos_validos_temporal(
                    conn=conn,
                )
            )

            turnos_ignorados = (
                exp_repository.obtener_turnos_ignorados(
                    conn=conn,
                )
            )

            tiempos["analizar_tmp_segundos"] = round(
                time.perf_counter() - inicio,
                2,
            )

            inicio = time.perf_counter()

            insertados = (
                exp_repository.insertar_apuestas_validas(
                    conn=conn,
                    archivo_origen=archivo_origen,
                )
            )

            tiempos["insert_real_segundos"] = round(
                time.perf_counter() - inicio,
                2,
            )

            ignorados_turno_invalido = (
                total_archivo
                - total_turnos_validos
            )

            ignorados_por_duplicado = max(
                total_turnos_validos
                - insertados,
                0,
            )

            inicio = time.perf_counter()

            exp_repository.registrar_carga(
                conn=conn,
                archivo_origen=archivo_origen,
                fecha=fecha,
            )

            tiempos["registrar_carga_segundos"] = round(
                time.perf_counter() - inicio,
                2,
            )

            inicio = time.perf_counter()

            cargados_turno = (
                exp_repository.contar_apuestas_por_fecha_turno(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            tiempos["validar_turno_segundos"] = round(
                time.perf_counter() - inicio,
                2,
            )

            if cargados_turno == 0:
                raise SinApuestasParaTurnoError(
                    "El archivo fue leído correctamente, "
                    "pero no contiene apuestas para "
                    f"fecha={fecha} y "
                    f"turno={turno_normalizado}"
                )

            inicio = time.perf_counter()

            marcar_exp_cargado(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
                archivo_exp=archivo_origen,
            )

            tiempos["marcar_exp_segundos"] = round(
                time.perf_counter() - inicio,
                2,
            )

        tiempos["total_service_segundos"] = round(
            time.perf_counter() - total_inicio,
            2,
        )

        logger.info(
            "Archivo EXP procesado: "
            "archivo=%s fecha=%s turno=%s "
            "total=%s insertados=%s "
            "turnos_invalidos=%s duplicados=%s",
            archivo_origen,
            fecha,
            turno_normalizado,
            total_archivo,
            insertados,
            ignorados_turno_invalido,
            ignorados_por_duplicado,
        )

        return {
            "ok": True,
            "archivo_origen": archivo_origen,
            "fecha": fecha,
            "turno": turno_normalizado,
            "total_archivo": total_archivo,
            "total_turnos_validos": (
                total_turnos_validos
            ),
            "insertados": insertados,
            "ignorados_turno_invalido": (
                ignorados_turno_invalido
            ),
            "ignorados_por_duplicado": (
                ignorados_por_duplicado
            ),
            "turnos_ignorados": turnos_ignorados,
            "cargados_turno": cargados_turno,
            "modo": (
                "copy_tmp_filter_valid_turns_"
                "insert_on_conflict_do_nothing"
            ),
            "tiempos_service": tiempos,
        }

    except AppException:
        raise

    except Exception as error:
        tiempos["total_service_segundos"] = round(
            time.perf_counter() - total_inicio,
            2,
        )

        logger.exception(
            "Error al procesar archivo EXP: "
            "archivo=%s fecha=%s turno=%s",
            archivo_origen,
            fecha,
            turno_normalizado,
        )

        raise ErrorProcesamientoExp(
            "Error al procesar el archivo EXP"
        ) from error