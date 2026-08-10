from typing import Any

from app.core.logger import logger
from app.core.transaction import transaction
from app.exceptions.base import AppException
from app.exceptions.comparacion_exceptions import (
    CalculoNoEjecutadoError,
    DbfNoCargadoError,
    ErrorComparacionError,
)
from app.repositories import (
    auditoria_repository,
    comparacion_repository,
)


def _convertir_ganador(
    item: tuple,
) -> dict[str, int]:
    (
        codigo_extracto,
        agencia,
        subagencia,
        maquina,
        cupon,
    ) = item

    return {
        "codigo_extracto": int(codigo_extracto),
        "agencia": int(agencia),
        "subagencia": int(subagencia),
        "maquina": int(maquina),
        "cupon": int(cupon),
    }


def _armar_comparacion_por_extracto(
    sistema: list[tuple],
    dbf: list[tuple],
) -> list[dict[str, int]]:
    sistema_dict = {
        int(codigo): int(cantidad)
        for codigo, cantidad in sistema
    }

    dbf_dict = {
        int(codigo): int(cantidad)
        for codigo, cantidad in dbf
    }

    codigos = sorted(
        set(sistema_dict)
        | set(dbf_dict)
    )

    return [
        {
            "codigo_extracto": codigo,
            "sistema": sistema_dict.get(
                codigo,
                0,
            ),
            "dbf": dbf_dict.get(
                codigo,
                0,
            ),
            "diferencia": (
                sistema_dict.get(codigo, 0)
                - dbf_dict.get(codigo, 0)
            ),
        }
        for codigo in codigos
    ]


def comparar_sistema_con_dbf(
    fecha: int,
    turno: str,
) -> dict[str, Any]:
    turno_normalizado = (
        turno.upper().strip()
    )

    try:
        with transaction() as conn:
            estado = (
                auditoria_repository.obtener_estado_por_fecha(
                    conn=conn,
                    fecha=fecha,
                )
            )

            estado_turno = next(
                (
                    row
                    for row in estado
                    if row[1] == turno_normalizado
                ),
                None,
            )

            if not estado_turno:
                raise CalculoNoEjecutadoError(
                    "No existe estado de auditoría para "
                    f"fecha={fecha}, "
                    f"turno={turno_normalizado}"
                )

            dbf_cargado = bool(
                estado_turno[4]
            )

            calculo_ejecutado = bool(
                estado_turno[5]
            )

            if not calculo_ejecutado:
                raise CalculoNoEjecutadoError()

            if not dbf_cargado:
                raise DbfNoCargadoError()

            ganadores_sistema = (
                comparacion_repository.obtener_ganadores_sistema(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            ganadores_dbf = (
                comparacion_repository.obtener_ganadores_dbf(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            set_sistema = set(
                ganadores_sistema
            )

            set_dbf = set(
                ganadores_dbf
            )

            coincidentes = (
                set_sistema
                & set_dbf
            )

            solo_sistema = (
                set_sistema
                - set_dbf
            )

            solo_dbf = (
                set_dbf
                - set_sistema
            )

            por_extracto_sistema = (
                comparacion_repository
                .obtener_aciertos_sistema_por_extracto(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            por_extracto_dbf = (
                comparacion_repository
                .obtener_aciertos_dbf_por_extracto(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            por_extracto = (
                _armar_comparacion_por_extracto(
                    sistema=por_extracto_sistema,
                    dbf=por_extracto_dbf,
                )
            )

            total_aciertos_sistema = sum(
                item["sistema"]
                for item in por_extracto
            )

            total_aciertos_dbf = sum(
                item["dbf"]
                for item in por_extracto
            )

            cupones_unicos_sistema = (
                comparacion_repository
                .contar_cupones_ganadores_unicos_sistema(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            cupones_unicos_dbf = (
                comparacion_repository
                .contar_cupones_ganadores_unicos_dbf(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            comparacion_repository.actualizar_cupones_dbf_resumen(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
                cantidad=cupones_unicos_dbf,
            )

        logger.info(
            "Comparación sistema/DBF: "
            "fecha=%s turno=%s "
            "aciertos_sistema=%s "
            "aciertos_dbf=%s "
            "cupones_sistema=%s "
            "cupones_dbf=%s",
            fecha,
            turno_normalizado,
            total_aciertos_sistema,
            total_aciertos_dbf,
            cupones_unicos_sistema,
            cupones_unicos_dbf,
        )

        return {
            "ok": True,
            "fecha": fecha,
            "turno": turno_normalizado,
            "aciertos": {
                "sistema": total_aciertos_sistema,
                "dbf": total_aciertos_dbf,
                "diferencia": (
                    total_aciertos_sistema
                    - total_aciertos_dbf
                ),
            },
            "cupones_ganadores_unicos": {
                "sistema": cupones_unicos_sistema,
                "dbf": cupones_unicos_dbf,
                "diferencia": (
                    cupones_unicos_sistema
                    - cupones_unicos_dbf
                ),
            },
            "por_extracto": por_extracto,
            "detalle": {
                "coincidentes": len(
                    coincidentes
                ),
                "solo_sistema": len(
                    solo_sistema
                ),
                "solo_dbf": len(
                    solo_dbf
                ),
            },
            "diferencias": {
                "solo_sistema": [
                    _convertir_ganador(item)
                    for item in sorted(
                        solo_sistema
                    )
                ],
                "solo_dbf": [
                    _convertir_ganador(item)
                    for item in sorted(
                        solo_dbf
                    )
                ],
            },
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error en comparación sistema/DBF: "
            "fecha=%s turno=%s",
            fecha,
            turno_normalizado,
        )

        raise ErrorComparacionError() from error