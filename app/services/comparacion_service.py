
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
from app.repositories import auditoria_repository, comparacion_repository
from app.services.auditoria_estado_service import validar_evento_abierto


CENTAVO = Decimal("0.01")
TOLERANCIA_MONTO = Decimal("100.00")


# ============================================================
# NORMALIZAR MONTOS
# ============================================================

def _decimal_monto(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# CONVERTIR GANADOR
# ============================================================

def _convertir_ganador(item: tuple) -> dict[str, int]:
    codigo_extracto, agencia, subagencia, maquina, cupon = item

    return {
        "codigo_extracto": int(codigo_extracto),
        "agencia": int(agencia),
        "subagencia": int(subagencia),
        "maquina": int(maquina),
        "cupon": int(cupon),
    }


# ============================================================
# COMPARACIÓN DE ACIERTOS POR EXTRACTO
# ============================================================

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

    codigos = sorted(set(sistema_dict) | set(dbf_dict))

    return [
        {
            "codigo_extracto": codigo,
            "sistema": sistema_dict.get(codigo, 0),
            "dbf": dbf_dict.get(codigo, 0),
            "diferencia": (
                sistema_dict.get(codigo, 0)
                - dbf_dict.get(codigo, 0)
            ),
        }
        for codigo in codigos
    ]


# ============================================================
# COMPARACIÓN DE MONTOS POR CUPÓN GLOBAL
# ============================================================

def _armar_comparacion_montos_cupones(
    sistema: list[tuple],
    dbf: list[tuple],
) -> dict[str, Any]:

    sistema_dict = {
        (
            int(agencia),
            int(subagencia),
            int(maquina),
            int(cupon),
        ): _decimal_monto(monto)
        for agencia, subagencia, maquina, cupon, monto in sistema
    }

    dbf_dict = {
        (
            int(agencia),
            int(subagencia),
            int(maquina),
            int(cupon),
        ): _decimal_monto(monto)
        for agencia, subagencia, maquina, cupon, monto in dbf
    }

    claves = sorted(set(sistema_dict) | set(dbf_dict))

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
            monto_sistema - monto_dbf
        ).quantize(
            CENTAVO,
            rounding=ROUND_HALF_UP,
        )

        diferencia_absoluta = abs(diferencia)

        if diferencia_absoluta == Decimal("0.00"):
            coincidentes_exactos += 1
            continue

        if diferencia_absoluta <= TOLERANCIA_MONTO:
            toleradas += 1
            continue

        agencia, subagencia, maquina, cupon = clave

        diferencias.append({
            "agencia": agencia,
            "subagencia": subagencia,
            "maquina": maquina,
            "cupon": cupon,
            "sistema": float(monto_sistema),
            "dbf": float(monto_dbf),
            "diferencia": float(diferencia),
            "diferencia_absoluta": float(diferencia_absoluta),
        })

    diferencias.sort(
        key=lambda item: item["diferencia_absoluta"],
        reverse=True,
    )

    diferencia_total = (
        monto_total_sistema - monto_total_dbf
    ).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )

    return {
        "monto_total_sistema": monto_total_sistema.quantize(
            CENTAVO,
            rounding=ROUND_HALF_UP,
        ),
        "monto_total_dbf": monto_total_dbf.quantize(
            CENTAVO,
            rounding=ROUND_HALF_UP,
        ),
        "diferencia_total": diferencia_total,
        "coincidentes_exactos": coincidentes_exactos,
        "toleradas": toleradas,
        "diferencias": diferencias,
    }


# ============================================================
# SERVICE PRINCIPAL
# ============================================================

def comparar_sistema_con_dbf(
    fecha: int,
    turno: str,
) -> dict[str, Any]:

    turno_normalizado = turno.upper().strip()

    try:
        with transaction() as conn:

            # ========================================================
            # VALIDAR EVENTO ABIERTO
            # ========================================================

            validar_evento_abierto(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
            )

            # ========================================================
            # VALIDAR PRECONDICIONES
            # ========================================================

            estado = auditoria_repository.obtener_estado_por_fecha(
                conn=conn,
                fecha=fecha,
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
                    f"fecha={fecha}, turno={turno_normalizado}"
                )

            dbf_cargado = bool(estado_turno[4])
            calculo_ejecutado = bool(estado_turno[5])

            if not calculo_ejecutado:
                raise CalculoNoEjecutadoError()

            if not dbf_cargado:
                raise DbfNoCargadoError()

            # ========================================================
            # OBTENER GANADORES
            # ========================================================

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

            set_sistema = set(ganadores_sistema)
            set_dbf = set(ganadores_dbf)

            coincidentes = set_sistema & set_dbf
            solo_sistema = set_sistema - set_dbf
            solo_dbf = set_dbf - set_sistema

            # ========================================================
            # IMPORTES APOSTADOS DE SOLO_SISTEMA
            # ========================================================

            filas_importes = (
                comparacion_repository
                .obtener_importes_apostados_cupones(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                    cupones=sorted(solo_sistema),
                )
            )

            importes_solo_sistema = {
                (
                    int(codigo_extracto),
                    int(agencia),
                    int(subagencia),
                    int(maquina),
                    int(cupon),
                ): float(_decimal_monto(importe))
                for (
                    codigo_extracto,
                    agencia,
                    subagencia,
                    maquina,
                    cupon,
                    importe,
                ) in filas_importes
            }

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

            por_extracto = _armar_comparacion_por_extracto(
                sistema=por_extracto_sistema,
                dbf=por_extracto_dbf,
            )

            # ========================================================
            # EXTRACTOS CON DIFERENCIAS EN CANTIDAD DE ACIERTOS
            # ========================================================

            extractos_con_diferencias = sorted(
                item["codigo_extracto"]
                for item in por_extracto
                if item["diferencia"] != 0
            )

            # ========================================================
            # TOTALES DE ACIERTOS
            # ========================================================

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
            # MONTOS GANADOS POR CUPÓN
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
            # IMPORTES APOSTADOS EN DIFERENCIAS DE MONTOS
            # ========================================================

            cupones_diferencias_montos = [
                (
                    item["agencia"],
                    item["subagencia"],
                    item["maquina"],
                    item["cupon"],
                )
                for item in comparacion_montos["diferencias"]
            ]

            filas_importes_montos = (
                comparacion_repository
                .obtener_importes_apostados_cupones_global(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                    cupones=cupones_diferencias_montos,
                )
            )

            importes_por_cupon = {
                (
                    int(agencia),
                    int(subagencia),
                    int(maquina),
                    int(cupon),
                ): float(_decimal_monto(importe))
                for (
                    agencia,
                    subagencia,
                    maquina,
                    cupon,
                    importe,
                ) in filas_importes_montos
            }

            for item in comparacion_montos["diferencias"]:
                clave = (
                    item["agencia"],
                    item["subagencia"],
                    item["maquina"],
                    item["cupon"],
                )

                item["importe_apostado"] = (
                    importes_por_cupon.get(clave)
                )

            # ========================================================
            # IMPORTES APOSTADOS POR EXTRACTO
            # ========================================================

            importes_apostados_db = (
                comparacion_repository
                .obtener_importes_apostados_por_extracto(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            importes_apostados_por_extracto = [
                {
                    "codigo_extracto": int(codigo_extracto),
                    "importe": float(_decimal_monto(importe)),
                }
                for codigo_extracto, importe
                in importes_apostados_db
            ]

            total_importes_apostados = sum(
                (
                    _decimal_monto(importe)
                    for _, importe in importes_apostados_db
                ),
                Decimal("0.00"),
            )

            # ========================================================
            # RESULTADO GENERAL
            # ========================================================

            hay_diferencias = (
                len(solo_sistema) > 0
                or len(solo_dbf) > 0
                or len(comparacion_montos["diferencias"]) > 0
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

            # ========================================================
            # MARCAR COMPARACIÓN EJECUTADA
            # ========================================================

            auditoria_repository.marcar_comparacion_ejecutada(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
                hay_diferencias=hay_diferencias,
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
            "importe_apostado=%s "
            "diferencias_monto=%s "
            "toleradas=%s "
            "hay_diferencias=%s",
            fecha,
            turno_normalizado,
            total_aciertos_sistema,
            total_aciertos_dbf,
            cupones_unicos_sistema,
            cupones_unicos_dbf,
            comparacion_montos["monto_total_sistema"],
            comparacion_montos["monto_total_dbf"],
            total_importes_apostados,
            len(comparacion_montos["diferencias"]),
            comparacion_montos["toleradas"],
            hay_diferencias,
        )

        # ============================================================
        # RESPONSE
        # ============================================================

        return {
            "ok": True,
            "fecha": fecha,
            "turno": turno_normalizado,
            "hay_diferencias": hay_diferencias,

            "aciertos": {
                "sistema": total_aciertos_sistema,
                "dbf": total_aciertos_dbf,
                "diferencia": (
                    total_aciertos_sistema - total_aciertos_dbf
                ),
            },

            "montos": {
                "sistema": float(
                    comparacion_montos["monto_total_sistema"]
                ),
                "dbf": float(
                    comparacion_montos["monto_total_dbf"]
                ),
                "diferencia": float(
                    comparacion_montos["diferencia_total"]
                ),
                "tolerancia": float(TOLERANCIA_MONTO),
            },

            "importes_apostados": {
                "total": float(total_importes_apostados),
                "por_extracto": importes_apostados_por_extracto,
            },

            "cupones_ganadores_unicos": {
                "sistema": cupones_unicos_sistema,
                "dbf": cupones_unicos_dbf,
                "diferencia": (
                    cupones_unicos_sistema - cupones_unicos_dbf
                ),
            },

            "por_extracto": por_extracto,

            "extractos_con_diferencias": (
                extractos_con_diferencias
            ),

            "detalle": {
                "coincidentes": len(coincidentes),
                "solo_sistema": len(solo_sistema),
                "solo_dbf": len(solo_dbf),
            },

            "detalle_montos": {
                "cupones_comparados": cupones_unicos_sistema,
                "coincidentes_exactos": (
                    comparacion_montos["coincidentes_exactos"]
                ),
                "diferencias_toleradas": (
                    comparacion_montos["toleradas"]
                ),
                "cupones_con_diferencia": len(
                    comparacion_montos["diferencias"]
                ),
            },

            "diferencias": {
                "solo_sistema": [
                    {
                        **_convertir_ganador(item),
                        "importe_apostado": (
                            importes_solo_sistema.get(item)
                        ),
                    }
                    for item in sorted(solo_sistema)
                ],
                "solo_dbf": [
                    _convertir_ganador(item)
                    for item in sorted(solo_dbf)
                ],
            },

            "diferencias_montos": (
                comparacion_montos["diferencias"]
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
