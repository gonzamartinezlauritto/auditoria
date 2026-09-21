from typing import Any

from app.core.logger import logger
from app.core.transaction import transaction
from app.exceptions.base import AppException
from app.exceptions.extractos_exceptions import (
    CantidadResultadosInvalidaError,
    ErrorProcesamientoResultados,
    NumeroResultadoInvalidoError,
    ResultadosVaciosError,
)
from app.repositories import (
    calculo_repository,
    extractos_repository,
)
from app.services.calculo_service import (
    calcular_extracto,
    validar_precondiciones_calculo,
)
from app.services.auditoria_estado_service import (
    marcar_resultados_cargados,
    validar_evento_abierto,
)


def normalizar_numero(
    numero: str,
) -> str:
    numero_normalizado = str(numero).strip()

    if not numero_normalizado.isdigit():
        raise NumeroResultadoInvalidoError(
            f"El resultado '{numero}' no es un número válido"
        )

    if len(numero_normalizado) > 4:
        raise NumeroResultadoInvalidoError(
            f"El resultado '{numero}' debe tener como máximo 4 dígitos"
        )

    return numero_normalizado.zfill(4)


def _mapear_reportes_calculo(
    rows: list[tuple],
) -> list[dict[str, Any]]:
    reportes = []

    for row in rows:
        (
            codigo_extracto,
            sorteo,
            cupones_jugados,
            recaudacion,
            importe_premiados,
            apuestas_premiadas,
        ) = row

        reportes.append(
            {
                "codigo_extracto": int(
                    codigo_extracto
                ),
                "sorteo": sorteo,
                "cupones_jugados": int(
                    cupones_jugados or 0
                ),
                "recaudacion": float(
                    recaudacion or 0
                ),
                "importe_premiados": float(
                    importe_premiados or 0
                ),
                "apuestas_premiadas": int(
                    apuestas_premiadas or 0
                ),
            }
        )

    return reportes


def cargar_extractos(
    fecha: int,
    turno: str,
    resultados: list[dict[str, Any]],
) -> dict[str, Any]:
    turno_normalizado = turno.upper().strip()

    if not resultados:
        raise ResultadosVaciosError()

    try:
        with transaction() as conn:

            # =============================================
            # PROTEGER EVENTOS CERRADOS
            # =============================================

            validar_evento_abierto(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
            )

            total_insertados = 0

            for item in resultados:
                codigo_extracto = int(
                    item["codigo_extracto"]
                )

                numeros = [
                    normalizar_numero(numero)
                    for numero in item["numeros"]
                ]

                if len(numeros) != 20:
                    raise CantidadResultadosInvalidaError(
                        "El extracto "
                        f"{codigo_extracto} contiene "
                        f"{len(numeros)} resultados. "
                        "Debe contener exactamente 20."
                    )

                extractos_repository.eliminar_resultados_extracto(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                    codigo_extracto=codigo_extracto,
                )

                for orden, numero in enumerate(
                    numeros,
                    start=1,
                ):
                    extractos_repository.insertar_resultado(
                        conn=conn,
                        fecha=fecha,
                        turno=turno_normalizado,
                        codigo_extracto=codigo_extracto,
                        orden=orden,
                        numero=numero,
                    )

                    total_insertados += 1

            marcar_resultados_cargados(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
            )

        logger.info(
            "Extractos cargados: fecha=%s turno=%s "
            "extractos=%s resultados=%s",
            fecha,
            turno_normalizado,
            len(resultados),
            total_insertados,
        )

        return {
            "ok": True,
            "fecha": fecha,
            "turno": turno_normalizado,
            "extractos_cargados": len(resultados),
            "resultados_insertados": total_insertados,
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error al cargar extractos: fecha=%s turno=%s",
            fecha,
            turno_normalizado,
        )

        raise ErrorProcesamientoResultados(
            "Error al cargar los extractos"
        ) from error


def obtener_extractos_por_fecha(
    fecha: int,
) -> dict[str, Any]:
    try:
        with transaction() as conn:
            rows = (
                extractos_repository.obtener_extractos_por_fecha(
                    conn=conn,
                    fecha=fecha,
                )
            )

        extractos_agrupados: dict[
            str,
            dict[int, dict[str, Any]],
        ] = {}

        for (
            turno,
            codigo_extracto,
            nombre_extracto,
            orden,
            numero,
        ) in rows:
            if turno not in extractos_agrupados:
                extractos_agrupados[turno] = {}

            if (
                codigo_extracto
                not in extractos_agrupados[turno]
            ):
                extractos_agrupados[turno][
                    codigo_extracto
                ] = {
                    "codigo_extracto": codigo_extracto,
                    "nombre_extracto": nombre_extracto,
                    "numeros": [],
                }

            extractos_agrupados[turno][
                codigo_extracto
            ]["numeros"].append(
                {
                    "orden": orden,
                    "numero": numero,
                }
            )

        return {
            "ok": True,
            "fecha": fecha,
            "resultados": extractos_agrupados,
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error al consultar extractos: fecha=%s",
            fecha,
        )

        raise ErrorProcesamientoResultados(
            "Error al consultar los extractos"
        ) from error


def modificar_extractos(
    fecha: int,
    turno: str,
    resultados: list[dict[str, Any]],
) -> dict[str, Any]:
    turno_normalizado = turno.upper().strip()

    if not resultados:
        raise ResultadosVaciosError()

    try:
        with transaction() as conn:

            # =============================================
            # PROTEGER EVENTOS CERRADOS
            # =============================================

            validar_evento_abierto(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
            )

            validar_precondiciones_calculo(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
            )

            codigos_recibidos: set[int] = set()
            reportes_recalculados = []

            for item in resultados:
                codigo_extracto = int(
                    item["codigo_extracto"]
                )

                # -----------------------------------------
                # EVITAR EXTRACTOS DUPLICADOS
                # -----------------------------------------

                if codigo_extracto in codigos_recibidos:
                    raise CantidadResultadosInvalidaError(
                        "El extracto "
                        f"{codigo_extracto} está repetido "
                        "en la solicitud."
                    )

                codigos_recibidos.add(
                    codigo_extracto
                )

                # -----------------------------------------
                # NORMALIZAR LOS 20 RESULTADOS
                # -----------------------------------------

                numeros_nuevos = [
                    normalizar_numero(numero)
                    for numero in item["numeros"]
                ]

                if len(numeros_nuevos) != 20:
                    raise CantidadResultadosInvalidaError(
                        "El extracto "
                        f"{codigo_extracto} contiene "
                        f"{len(numeros_nuevos)} resultados. "
                        "Debe contener exactamente 20."
                    )

                # -----------------------------------------
                # OBTENER LOS ACTUALES
                # -----------------------------------------

                actuales = (
                    extractos_repository.obtener_resultados_extracto(
                        conn=conn,
                        fecha=fecha,
                        turno=turno_normalizado,
                        codigo_extracto=codigo_extracto,
                    )
                )

                if not actuales:
                    raise ResultadosVaciosError()

                if len(actuales) != 20:
                    raise CantidadResultadosInvalidaError(
                        "El extracto "
                        f"{codigo_extracto} posee "
                        f"{len(actuales)} resultados "
                        "guardados. Se esperaban 20."
                    )

                numeros_actuales = [
                    str(numero).strip().zfill(4)
                    for _orden, numero in actuales
                ]

                # -----------------------------------------
                # SI NO CAMBIÓ, NO RECALCULAMOS
                # -----------------------------------------

                if numeros_actuales == numeros_nuevos:
                    logger.info(
                        "Extracto sin cambios: "
                        "fecha=%s turno=%s extracto=%s",
                        fecha,
                        turno_normalizado,
                        codigo_extracto,
                    )

                    continue

                # -----------------------------------------
                # REEMPLAZAR RESULTADOS
                # -----------------------------------------

                extractos_repository.eliminar_resultados_extracto(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                    codigo_extracto=codigo_extracto,
                )

                for orden, numero in enumerate(
                    numeros_nuevos,
                    start=1,
                ):
                    extractos_repository.insertar_resultado(
                        conn=conn,
                        fecha=fecha,
                        turno=turno_normalizado,
                        codigo_extracto=codigo_extracto,
                        orden=orden,
                        numero=numero,
                    )

                # -----------------------------------------
                # RECALCULAR SOLO ESE EXTRACTO
                # -----------------------------------------

                reporte = calcular_extracto(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                    cod=codigo_extracto,
                )

                reportes_recalculados.append(
                    reporte
                )

                logger.info(
                    "Extracto recalculado: "
                    "fecha=%s turno=%s extracto=%s",
                    fecha,
                    turno_normalizado,
                    codigo_extracto,
                )

            # =============================================
            # RECALCULAR CUPONES GANADORES GLOBALES
            # =============================================

            cupones_ganadores_unicos = (
                calculo_repository.contar_cupones_ganadores_unicos(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            # =============================================
            # ACTUALIZAR RESUMEN DE EXTRACTOS MODIFICADOS
            # =============================================

            for reporte in reportes_recalculados:
                calculo_repository.guardar_resumen_extracto(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                    reporte=reporte,
                    cupones_ganadores_unicos=(
                        cupones_ganadores_unicos
                    ),
                )

            # =============================================
            # EL TOTAL DE CUPONES ES GLOBAL
            # =============================================

            calculo_repository.actualizar_cupones_ganadores_unicos_resumen(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
                cantidad=cupones_ganadores_unicos,
            )

            # =============================================
            # DEVOLVER TODOS LOS EXTRACTOS
            # =============================================

            rows = (
                calculo_repository.obtener_reportes_turno(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            reportes = _mapear_reportes_calculo(
                rows
            )

        logger.info(
            "Modificación de extractos finalizada: "
            "fecha=%s turno=%s "
            "extractos_recibidos=%s "
            "extractos_recalculados=%s",
            fecha,
            turno_normalizado,
            len(codigos_recibidos),
            len(reportes_recalculados),
        )

        return {
            "ok": True,
            "fecha": fecha,
            "turno": turno_normalizado,
            "reportes": reportes,
            "cupones_ganadores_unicos": (
                cupones_ganadores_unicos
            ),
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error al modificar extractos: "
            "fecha=%s turno=%s",
            fecha,
            turno_normalizado,
        )

        raise ErrorProcesamientoResultados(
            "Error al modificar los extractos"
        ) from error