from typing import Any

from app.core.logger import logger
from app.core.transaction import transaction
from app.exceptions.base import AppException
from app.exceptions.resultados_exceptions import (
    CantidadResultadosInvalidaError,
    ErrorProcesamientoResultados,
    NumeroResultadoInvalidoError,
    ResultadosVaciosError,
)
from app.repositories import resultados_repository
from app.services.auditoria_estado_service import (
    marcar_resultados_cargados,
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


def cargar_resultados(
    fecha: int,
    turno: str,
    resultados: list[dict[str, Any]],
) -> dict[str, Any]:
    turno_normalizado = turno.upper().strip()

    if not resultados:
        raise ResultadosVaciosError()

    try:
        with transaction() as conn:
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

                resultados_repository.eliminar_resultados_extracto(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                    codigo_extracto=codigo_extracto,
                )

                for orden, numero in enumerate(
                    numeros,
                    start=1,
                ):
                    resultados_repository.insertar_resultado(
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
            "Resultados cargados: fecha=%s turno=%s "
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
            "Error al cargar resultados: fecha=%s turno=%s",
            fecha,
            turno_normalizado,
        )

        raise ErrorProcesamientoResultados(
            "Error al cargar los resultados"
        ) from error


def obtener_resultados_por_fecha(
    fecha: int,
) -> dict[str, Any]:
    try:
        with transaction() as conn:
            rows = (
                resultados_repository.obtener_resultados_por_fecha(
                    conn=conn,
                    fecha=fecha,
                )
            )

        resultados_agrupados: dict[str, dict[int, dict[str, Any]]] = {}

        for (
            turno,
            codigo_extracto,
            nombre_extracto,
            orden,
            numero,
        ) in rows:
            if turno not in resultados_agrupados:
                resultados_agrupados[turno] = {}

            if (
                codigo_extracto
                not in resultados_agrupados[turno]
            ):
                resultados_agrupados[turno][
                    codigo_extracto
                ] = {
                    "codigo_extracto": codigo_extracto,
                    "nombre_extracto": nombre_extracto,
                    "numeros": [],
                }

            resultados_agrupados[turno][
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
            "resultados": resultados_agrupados,
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error al consultar resultados: fecha=%s",
            fecha,
        )

        raise ErrorProcesamientoResultados(
            "Error al consultar los resultados"
        ) from error