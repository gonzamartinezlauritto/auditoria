from decimal import Decimal, ROUND_HALF_UP
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


CENTAVO = Decimal("0.01")

# Diferencias de hasta $100 inclusive
# NO se consideran diferencias de auditoría.
TOLERANCIA_MONTO = Decimal("100.00")


def _decimal_monto(
    value,
) -> Decimal:
    return Decimal(
        str(value or 0)
    ).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
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


def _armar_comparacion_montos_cupones(
    sistema: list[tuple],
    dbf: list[tuple],
) -> dict[str, Any]:
    """
    Compara los montos a nivel CUPÓN GLOBAL.

    Clave:
    (
        agencia,
        subagencia,
        maquina,
        cupon
    )

    Una diferencia absoluta <= $100
    se considera tolerada.
    """

    sistema_dict = {
        (
            int(agencia),
            int(subagencia),
            int(maquina),
            int(cupon),
        ): _decimal_monto(monto)
        for (
            agencia,
            subagencia,
            maquina,
            cupon,
            monto,
        ) in sistema
    }

    dbf_dict = {
        (
            int(agencia),
            int(subagencia),
            int(maquina),
            int(cupon),
        ): _decimal_monto(monto)
        for (
            agencia,
            subagencia,
            maquina,
            cupon,
            monto,
        ) in dbf
    }

    claves = sorted(
        set(sistema_dict)
        | set(dbf_dict)
    )

    diferencias = []
    toleradas = 0
    coincidentes_exactos = 0

    monto_total_sistema = sum(
        sistema_dict.values(),
        Decimal("0.00"),
    )

    monto_total_dbf = sum(
        dbf_dict.values(),
        Decimal("0.00"),
    )

    for clave in claves:
        monto_sistema = sistema_dict.get(
            clave,
            Decimal("0.00"),
        )

        monto_dbf = dbf_dict.get(
            clave,
            Decimal("0.00"),
        )

        diferencia = (
            monto_sistema
            - monto_dbf
        ).quantize(
            CENTAVO,
            rounding=ROUND_HALF_UP,
        )

        diferencia_absoluta = abs(
            diferencia
        )

        # Coincidencia exacta
        if diferencia_absoluta == Decimal("0.00"):
            coincidentes_exactos += 1
            continue

        # Diferencia tolerada:
        # hasta $100 inclusive NO corre como diferencia.
        if diferencia_absoluta <= TOLERANCIA_MONTO:
            toleradas += 1
            continue

        (
            agencia,
            subagencia,
            maquina,
            cupon,
        ) = clave

        diferencias.append(
            {
                "agencia": agencia,
                "subagencia": subagencia,
                "maquina": maquina,
                "cupon": cupon,
                "sistema": float(
                    monto_sistema
                ),
                "dbf": float(
                    monto_dbf
                ),
                "diferencia": float(
                    diferencia
                ),
                "diferencia_absoluta": float(
                    diferencia_absoluta
                ),
            }
        )

    # Ordenamos primero las diferencias más grandes.
    diferencias.sort(
        key=lambda item: item[
            "diferencia_absoluta"
        ],
        reverse=True,
    )

    diferencia_total = (
        monto_total_sistema
        - monto_total_dbf
    ).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )

    return {
        "monto_total_sistema": (
            monto_total_sistema.quantize(
                CENTAVO,
                rounding=ROUND_HALF_UP,
            )
        ),
        "monto_total_dbf": (
            monto_total_dbf.quantize(
                CENTAVO,
                rounding=ROUND_HALF_UP,
            )
        ),
        "diferencia_total": diferencia_total,
        "coincidentes_exactos": coincidentes_exactos,
        "toleradas": toleradas,
        "diferencias": diferencias,
    }


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
                auditoria_repository
                .obtener_estado_por_fecha(
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

            # ========================================================
            # GANADORES SISTEMA / DBF
            # ========================================================

            ganadores_sistema = (
                comparacion_repository
                .obtener_ganadores_sistema(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            ganadores_dbf = (
                comparacion_repository
                .obtener_ganadores_dbf(
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

            # ========================================================
            # ACIERTOS POR EXTRACTO
            # ========================================================

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

            # ========================================================
            # CUPONES GANADORES ÚNICOS
            # ========================================================

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

            # ========================================================
            # MONTOS POR CUPÓN
            # ========================================================

            montos_sistema_cupon = (
                comparacion_repository
                .obtener_montos_sistema_por_cupon(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            montos_dbf_cupon = (
                comparacion_repository
                .obtener_montos_dbf_por_cupon(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            comparacion_montos = (
                _armar_comparacion_montos_cupones(
                    sistema=montos_sistema_cupon,
                    dbf=montos_dbf_cupon,
                )
            )

            # ========================================================
            # ACTUALIZAR RESUMEN
            # ========================================================

            comparacion_repository.actualizar_cupones_dbf_resumen(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
                cantidad=cupones_unicos_dbf,
            )

        # ============================================================
        # LOG
        # ============================================================

        logger.info(
            "Comparación sistema/DBF: "
            "fecha=%s turno=%s "
            "aciertos_sistema=%s "
            "aciertos_dbf=%s "
            "cupones_sistema=%s "
            "cupones_dbf=%s "
            "monto_sistema=%s "
            "monto_dbf=%s "
            "diferencias_monto=%s "
            "toleradas=%s",
            fecha,
            turno_normalizado,
            total_aciertos_sistema,
            total_aciertos_dbf,
            cupones_unicos_sistema,
            cupones_unicos_dbf,
            comparacion_montos[
                "monto_total_sistema"
            ],
            comparacion_montos[
                "monto_total_dbf"
            ],
            len(
                comparacion_montos[
                    "diferencias"
                ]
            ),
            comparacion_montos[
                "toleradas"
            ],
        )

        # ============================================================
        # RESPONSE
        # ============================================================

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

            "montos": {
                "sistema": float(
                    comparacion_montos[
                        "monto_total_sistema"
                    ]
                ),
                "dbf": float(
                    comparacion_montos[
                        "monto_total_dbf"
                    ]
                ),
                "diferencia": float(
                    comparacion_montos[
                        "diferencia_total"
                    ]
                ),
                "tolerancia": float(
                    TOLERANCIA_MONTO
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

            "detalle_montos": {
                "cupones_comparados": (
                    cupones_unicos_sistema
                ),
                "coincidentes_exactos": (
                    comparacion_montos[
                        "coincidentes_exactos"
                    ]
                ),
                "diferencias_toleradas": (
                    comparacion_montos[
                        "toleradas"
                    ]
                ),
                "cupones_con_diferencia": len(
                    comparacion_montos[
                        "diferencias"
                    ]
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

            "diferencias_montos": (
                comparacion_montos[
                    "diferencias"
                ]
            ),
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