from typing import Any

from psycopg2.extensions import connection

from app.core.logger import logger
from app.core.transaction import transaction
from app.exceptions.base import AppException
from app.exceptions.auditoria_exceptions import (
    EventoCerradoError,
    EventoIncompletoError,
    EventoNoEncontradoError,
    EventoYaAbiertoError,
    EventoYaCerradoError,
    MotivoReaperturaRequeridoError,
)
from app.repositories import auditoria_repository


# =========================================================
# MARCADO DE ETAPAS
# =========================================================

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


def marcar_comparacion_ejecutada(
    conn: connection,
    fecha: int,
    turno: str,
) -> None:
    auditoria_repository.marcar_comparacion_ejecutada(
        conn=conn,
        fecha=fecha,
        turno=turno,
    )


# =========================================================
# INVALIDACIÓN DE ETAPAS
# =========================================================

def invalidar_comparacion(
    conn: connection,
    fecha: int,
    turno: str,
) -> None:
    auditoria_repository.invalidar_comparacion(
        conn=conn,
        fecha=fecha,
        turno=turno,
    )


def invalidar_calculo_y_comparacion(
    conn: connection,
    fecha: int,
    turno: str,
) -> None:
    auditoria_repository.invalidar_calculo_y_comparacion(
        conn=conn,
        fecha=fecha,
        turno=turno,
    )


# =========================================================
# VALIDAR EVENTO ABIERTO
# =========================================================

def validar_evento_abierto(
    conn: connection,
    fecha: int,
    turno: str,
) -> None:
    turno_normalizado = turno.upper().strip()

    evento = auditoria_repository.obtener_evento(
        conn=conn,
        fecha=fecha,
        turno=turno_normalizado,
    )

    # Si todavía no existe el registro significa que
    # estamos comenzando un evento nuevo.
    if not evento:
        return

    evento_cerrado = bool(
        evento[7]
    )

    if evento_cerrado:
        raise EventoCerradoError(
            (
                f"El evento {fecha} / {turno_normalizado} "
                "se encuentra cerrado. Debe ser reabierto "
                "antes de modificarlo."
            )
        )


# =========================================================
# CERRAR EVENTO
# =========================================================

def cerrar_evento(
    fecha: int,
    turno: str,
    usuario: str,
) -> dict[str, Any]:
    turno_normalizado = turno.upper().strip()

    try:
        with transaction() as conn:
            evento = auditoria_repository.obtener_evento(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
            )

            if not evento:
                raise EventoNoEncontradoError(
                    (
                        "No existe un evento de auditoría "
                        f"para fecha={fecha}, "
                        f"turno={turno_normalizado}."
                    )
                )

            (
                _fecha_sorteo,
                _turno,
                exp_cargado,
                resultados_cargados,
                dbf_cargado,
                calculo_ejecutado,
                comparacion_ejecutada,
                evento_cerrado,
                _fecha_comparacion,
                _fecha_cierre,
                _cerrado_por,
                _fecha_reapertura,
                _reabierto_por,
                _motivo_reapertura,
            ) = evento

            if evento_cerrado:
                raise EventoYaCerradoError(
                    (
                        f"El evento {fecha} / "
                        f"{turno_normalizado} "
                        "ya se encuentra cerrado."
                    )
                )

            etapas_pendientes: list[str] = []

            if not exp_cargado:
                etapas_pendientes.append(
                    "EXP"
                )

            if not resultados_cargados:
                etapas_pendientes.append(
                    "resultados"
                )

            if not calculo_ejecutado:
                etapas_pendientes.append(
                    "cálculo"
                )

            if not dbf_cargado:
                etapas_pendientes.append(
                    "DBF"
                )

            if not comparacion_ejecutada:
                etapas_pendientes.append(
                    "comparación"
                )

            if etapas_pendientes:
                raise EventoIncompletoError(
                    (
                        "No se puede cerrar el evento. "
                        "Faltan completar las siguientes etapas: "
                        + ", ".join(etapas_pendientes)
                        + "."
                    )
                )

            auditoria_repository.cerrar_evento(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
                usuario=usuario,
            )

            auditoria_repository.registrar_historial_evento(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
                accion="CIERRE",
                usuario=usuario,
            )

        logger.info(
            "Evento de auditoría cerrado: "
            "fecha=%s turno=%s usuario=%s",
            fecha,
            turno_normalizado,
            usuario,
        )

        return {
            "ok": True,
            "fecha": fecha,
            "turno": turno_normalizado,
            "evento_cerrado": True,
            "cerrado_por": usuario,
            "message": (
                "Evento de auditoría cerrado correctamente."
            ),
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error al cerrar evento de auditoría: "
            "fecha=%s turno=%s",
            fecha,
            turno_normalizado,
        )

        raise error


# =========================================================
# REABRIR EVENTO
# =========================================================

def reabrir_evento(
    fecha: int,
    turno: str,
    usuario: str,
    motivo: str,
) -> dict[str, Any]:
    turno_normalizado = turno.upper().strip()
    motivo_normalizado = motivo.strip()

    if not motivo_normalizado:
        raise MotivoReaperturaRequeridoError()

    try:
        with transaction() as conn:
            evento = auditoria_repository.obtener_evento(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
            )

            if not evento:
                raise EventoNoEncontradoError(
                    (
                        "No existe un evento de auditoría "
                        f"para fecha={fecha}, "
                        f"turno={turno_normalizado}."
                    )
                )

            evento_cerrado = bool(
                evento[7]
            )

            if not evento_cerrado:
                raise EventoYaAbiertoError(
                    (
                        f"El evento {fecha} / "
                        f"{turno_normalizado} "
                        "ya se encuentra abierto."
                    )
                )

            auditoria_repository.reabrir_evento(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
                usuario=usuario,
                motivo=motivo_normalizado,
            )

            auditoria_repository.registrar_historial_evento(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
                accion="REAPERTURA",
                usuario=usuario,
                motivo=motivo_normalizado,
            )

        logger.info(
            "Evento de auditoría reabierto: "
            "fecha=%s turno=%s usuario=%s motivo=%s",
            fecha,
            turno_normalizado,
            usuario,
            motivo_normalizado,
        )

        return {
            "ok": True,
            "fecha": fecha,
            "turno": turno_normalizado,
            "evento_cerrado": False,
            "reabierto_por": usuario,
            "motivo_reapertura": motivo_normalizado,
            "message": (
                "Evento de auditoría reabierto correctamente. "
                "La comparación anterior fue invalidada y deberá "
                "ejecutarse nuevamente antes de cerrar el evento."
            ),
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error al reabrir evento de auditoría: "
            "fecha=%s turno=%s",
            fecha,
            turno_normalizado,
        )

        raise error


# =========================================================
# ESTADO POR FECHA
# =========================================================

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
                comparacion_ejecutada,
                fecha_comparacion,
                evento_cerrado,
                fecha_cierre,
                cerrado_por,
                fecha_reapertura,
                reabierto_por,
                motivo_reapertura,
                updated_at,
            ) = row

            turnos.append(
                {
                    "turno": turno,

                    "exp_cargado": bool(
                        exp_cargado
                    ),

                    "resultados_cargados": bool(
                        resultados_cargados
                    ),

                    "dbf_cargado": bool(
                        dbf_cargado
                    ),

                    "calculo_ejecutado": bool(
                        calculo_ejecutado
                    ),

                    "comparacion_ejecutada": bool(
                        comparacion_ejecutada
                    ),

                    "evento_cerrado": bool(
                        evento_cerrado
                    ),

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

                    "fecha_comparacion": (
                        str(fecha_comparacion)
                        if fecha_comparacion
                        else None
                    ),

                    "fecha_cierre": (
                        str(fecha_cierre)
                        if fecha_cierre
                        else None
                    ),

                    "cerrado_por": cerrado_por,

                    "fecha_reapertura": (
                        str(fecha_reapertura)
                        if fecha_reapertura
                        else None
                    ),

                    "reabierto_por": reabierto_por,

                    "motivo_reapertura": (
                        motivo_reapertura
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
            "Error al obtener estado de auditoría: "
            "fecha=%s",
            fecha,
        )

        raise error


# =========================================================
# HISTORIAL DEL EVENTO
# =========================================================

def obtener_historial_evento(
    fecha: int,
    turno: str,
) -> dict[str, Any]:
    turno_normalizado = turno.upper().strip()

    try:
        with transaction() as conn:
            rows = auditoria_repository.obtener_historial_evento(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
            )

        historial: list[dict[str, Any]] = []

        for row in rows:
            (
                historial_id,
                fecha_sorteo,
                turno_evento,
                accion,
                usuario,
                motivo,
                created_at,
            ) = row

            historial.append(
                {
                    "id": int(
                        historial_id
                    ),
                    "fecha": int(
                        fecha_sorteo
                    ),
                    "turno": turno_evento,
                    "accion": accion,
                    "usuario": usuario,
                    "motivo": motivo,
                    "fecha_operacion": (
                        str(created_at)
                        if created_at
                        else None
                    ),
                }
            )

        return {
            "ok": True,
            "fecha": fecha,
            "turno": turno_normalizado,
            "historial": historial,
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error al obtener historial de evento: "
            "fecha=%s turno=%s",
            fecha,
            turno_normalizado,
        )

        raise error