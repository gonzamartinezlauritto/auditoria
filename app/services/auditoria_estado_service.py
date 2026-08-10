from typing import Any

from psycopg2.extensions import connection

from app.core.logger import logger
from app.core.transaction import transaction
from app.exceptions.base import AppException
from app.repositories import auditoria_repository


def marcar_exp_cargado(
    conn: connection,
    fecha: int,
    turno: str,
    archivo_exp: str,
) -> None:
    auditoria_repository.marcar_exp_cargado(
        conn=conn,
        fecha=fecha,
        turno=turno,
        archivo_exp=archivo_exp,
    )


def marcar_dbf_cargado(
    conn: connection,
    fecha: int,
    turno: str,
    archivo_dbf: str,
) -> None:
    auditoria_repository.marcar_dbf_cargado(
        conn=conn,
        fecha=fecha,
        turno=turno,
        archivo_dbf=archivo_dbf,
    )


def marcar_resultados_cargados(
    conn: connection,
    fecha: int,
    turno: str,
) -> None:
    auditoria_repository.marcar_resultados_cargados(
        conn=conn,
        fecha=fecha,
        turno=turno,
    )


def marcar_calculo_ejecutado(
    conn: connection,
    fecha: int,
    turno: str,
) -> None:
    auditoria_repository.marcar_calculo_ejecutado(
        conn=conn,
        fecha=fecha,
        turno=turno,
    )


def obtener_estado_por_fecha(
    fecha: int,
) -> dict[str, Any]:
    try:
        with transaction() as conn:
            rows = auditoria_repository.obtener_estado_por_fecha(
                conn=conn,
                fecha=fecha,
            )

        turnos: list[dict[str, Any]] = []

        for row in rows:
            (
                _fecha_sorteo,
                turno,
                exp_cargado,
                resultados_cargados,
                dbf_cargado,
                calculo_ejecutado,
                archivo_exp,
                archivo_dbf,
                fecha_exp,
                fecha_dbf,
                fecha_calculo,
                updated_at,
            ) = row

            turnos.append(
                {
                    "turno": turno,
                    "exp_cargado": exp_cargado,
                    "resultados_cargados": resultados_cargados,
                    "dbf_cargado": dbf_cargado,
                    "calculo_ejecutado": calculo_ejecutado,
                    "archivo_exp": archivo_exp,
                    "archivo_dbf": archivo_dbf,
                    "fecha_exp": (
                        str(fecha_exp)
                        if fecha_exp
                        else None
                    ),
                    "fecha_dbf": (
                        str(fecha_dbf)
                        if fecha_dbf
                        else None
                    ),
                    "fecha_calculo": (
                        str(fecha_calculo)
                        if fecha_calculo
                        else None
                    ),
                    "updated_at": (
                        str(updated_at)
                        if updated_at
                        else None
                    ),
                }
            )

        return {
            "ok": True,
            "fecha": fecha,
            "turnos": turnos,
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error al obtener estado de auditoría: fecha=%s",
            fecha,
        )

        raise error