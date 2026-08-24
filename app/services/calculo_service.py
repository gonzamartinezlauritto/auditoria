from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.core.logger import logger
from app.exceptions.base import AppException
from app.exceptions.calculo_exceptions import (
    ErrorProcesamientoCalculo,
    ExtractoNoEncontradoError,
    PrecondicionesCalculoError,
    ResultadosNoEncontradosError,
    SinExtractosParaCalcularError,
)
from app.core.transaction import transaction
from app.repositories import calculo_repository
from app.services.auditoria_estado_service import (
    marcar_calculo_ejecutado,
)
from app.services.premios_service import (
    buscar_aproximado,
    calcular_premio,
    cantidad_puestos,
    es_a_la_cabeza,
    limpiar_numero,
    normalizar_resultado,
    obtener_hits,
    obtener_multiplicador,
    redondear_a_diez_centavos,
)
from app.services.redoblona_service import (
    ajustar_rango_detalle_redoblona,
    calcular_tope_redoblona,
    marcar_redoblonas_por_patron,
)


def validar_precondiciones_calculo(
    conn,
    fecha: int,
    turno: str,
) -> None:
    estado = calculo_repository.obtener_estado_cargas(
        conn=conn,
        fecha=fecha,
        turno=turno,
    )

    if not estado:
        raise PrecondicionesCalculoError(
            "No hay cargas registradas para "
            f"fecha={fecha}, turno={turno}"
        )

    (
        exp_cargado,
        resultados_cargados,
        _dbf_cargado,
    ) = estado

    if not exp_cargado:
        raise PrecondicionesCalculoError(
            "No se puede calcular: "
            "falta cargar el EXP para "
            f"fecha={fecha}, turno={turno}"
        )

    if not resultados_cargados:
        raise PrecondicionesCalculoError(
            "No se puede calcular: "
            "faltan cargar los resultados para "
            f"fecha={fecha}, turno={turno}"
        )


def _mapear_apuestas(
    rows: list[tuple],
) -> list[dict[str, Any]]:
    apuestas = []

    for row in rows:
        apuestas.append(
            {
                "id": row[0],
                "n_apues": row[1],
                "n_maqre": row[2],
                "n_agent": row[3],
                "n_subag": row[4],
                "n_maqui": row[5],
                "n_cupon": row[6],
                "n_linea": row[7],
                "n_femis": row[8],
                "c_hemis": row[9],
                "c_ecupon": row[10],
                "n_fsorteo": row[11],
                "n_codlot": row[12],
                "c_tsorteo": row[13],
                "n_alcdes": int(
                    row[14] or 0
                ),
                "n_alchas": int(
                    row[15] or 0
                ),
                "c_nroapos": limpiar_numero(
                    row[16]
                ),
                "n_impapos": Decimal(
                    str(row[17] or 0)
                ).quantize(
                    Decimal("0.01")
                ),
                "n_nodef": int(
                    row[18] or 0
                ),
                "n_codext": row[19],
                "es_redoblona_base": bool(
                    row[20]
                ),
                "es_redoblona_detalle": bool(
                    row[21]
                ),
                "linea_base_id": row[22],
                "redoblona_grupo": row[23],
            }
        )

    return apuestas


def _agrupar_redoblonas(
    apuestas: list[dict[str, Any]],
) -> dict[Any, list[dict[str, Any]]]:
    grupos = {}

    for apuesta in apuestas:
        grupo = apuesta["redoblona_grupo"]

        if grupo is not None:
            grupos.setdefault(
                grupo,
                [],
            ).append(
                apuesta
            )

    return grupos


def _procesar_redoblona(
    conn,
    *,
    actual: dict[str, Any],
    detalle: dict[str, Any],
    resultados: list[tuple],
    fecha: int,
    codigo_extracto: int,
    p4,
    p3,
    p2,
    p1,
    tope_redoblona: Decimal,
) -> None:
    numero = actual["c_nroapos"]
    importe = actual["n_impapos"]
    desde = actual["n_alcdes"]
    hasta = actual["n_alchas"]

    hits_base = obtener_hits(
        numero,
        desde,
        hasta,
        resultados,
    )

    if not hits_base:
        return

    (
        orden_base,
        _resultado_base,
        cifras_base,
    ) = hits_base[0]

    multiplicador_base = obtener_multiplicador(
        cifras_base,
        p4,
        p3,
        p2,
        p1,
    )

    if multiplicador_base <= 0:
        return

    puestos_base = cantidad_puestos(
        desde,
        hasta,
    )

    premio_base_unitario = calcular_premio(
        importe,
        multiplicador_base,
        puestos_base,
    )

    repeticiones_base = len(
        hits_base
    )

    premio_base_total = (
        premio_base_unitario
        * Decimal(
            repeticiones_base
        )
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    (
        detalle_desde,
        detalle_hasta,
    ) = ajustar_rango_detalle_redoblona(
        desde,
        hasta,
        detalle["n_alcdes"],
        detalle["n_alchas"],
    )

    hits_detalle = obtener_hits(
        detalle["c_nroapos"],
        detalle_desde,
        detalle_hasta,
        resultados,
    )

    hits_detalle = [
        hit
        for hit in hits_detalle
        if hit[0] != orden_base
    ]

    if not hits_detalle:
        return

    (
        orden_detalle,
        resultado_detalle,
        cifras_detalle,
    ) = hits_detalle[0]

    multiplicador_detalle = obtener_multiplicador(
        cifras_detalle,
        p4,
        p3,
        p2,
        p1,
    )

    if multiplicador_detalle <= 0:
        return

    puestos_detalle = cantidad_puestos(
        detalle_desde,
        detalle_hasta,
    )

    premio_detalle_unitario = calcular_premio(
        premio_base_total,
        multiplicador_detalle,
        puestos_detalle,
    )

    repeticiones_detalle = len(
        hits_detalle
    )

    premio_detalle_total = (
        premio_detalle_unitario
        * Decimal(
            repeticiones_detalle
        )
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    tope = calcular_tope_redoblona(
        importe,
        desde,
        hasta,
        tope_redoblona,
    )

    premio_final = min(
        premio_detalle_total,
        tope,
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    if premio_final <= 0:
        return

    calculo_repository.insertar_premio(
        conn=conn,
        data=(
            actual["id"],
            fecha,
            codigo_extracto,
            (
                f"{numero}/"
                f"{detalle['c_nroapos']}"
            ),
            normalizar_resultado(
                resultado_detalle
            ),
            orden_detalle,
            cifras_detalle,
            importe,
            multiplicador_detalle,
            premio_final,
            "redoblona",
            detalle["id"],
            premio_base_total,
        ),
    )


def _procesar_apuesta_normal(
    conn,
    *,
    actual: dict[str, Any],
    resultados: list[tuple],
    fecha: int,
    codigo_extracto: int,
    p4,
    p3,
    p2,
    p1,
    aprox4: Decimal,
    aprox3: Decimal,
) -> None:
    numero = actual["c_nroapos"]
    importe = actual["n_impapos"]
    desde = actual["n_alcdes"]
    hasta = actual["n_alchas"]

    if importe <= 0:
        return

    hits = obtener_hits(
        numero,
        desde,
        hasta,
        resultados,
    )

    for (
        orden,
        resultado,
        cifras,
    ) in hits:
        multiplicador = obtener_multiplicador(
            cifras,
            p4,
            p3,
            p2,
            p1,
        )

        if multiplicador <= 0:
            continue

        puestos = cantidad_puestos(
            desde,
            hasta,
        )

        premio = calcular_premio(
            importe,
            multiplicador,
            puestos,
        )

        if premio <= 0:
            continue

        calculo_repository.insertar_premio(
            conn=conn,
            data=(
                actual["id"],
                fecha,
                codigo_extracto,
                numero,
                normalizar_resultado(
                    resultado
                ),
                orden,
                cifras,
                importe,
                multiplicador,
                premio,
                "normal",
                None,
                None,
            ),
        )

    if not es_a_la_cabeza(
        desde,
        hasta,
    ):
        return

    aproximado = buscar_aproximado(
        numero,
        resultados,
        aprox4,
        aprox3,
    )

    if not aproximado:
        return

    (
        tipo,
        orden,
        resultado,
        cifras,
        multiplicador,
    ) = aproximado

    premio = (
        importe
        * multiplicador
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    if premio <= 0:
        return

    calculo_repository.insertar_premio(
        conn=conn,
        data=(
            actual["id"],
            fecha,
            codigo_extracto,
            numero,
            normalizar_resultado(
                resultado
            ),
            orden,
            cifras,
            importe,
            multiplicador,
            premio,
            tipo,
            None,
            None,
        ),
    )


def calcular_extracto(
    conn,
    fecha: int,
    turno: str,
    cod: int,
) -> dict[str, Any]:
    turno_normalizado = turno.upper().strip()

    extracto = calculo_repository.obtener_extracto(
        conn=conn,
        codigo_extracto=cod,
    )

    if not extracto:
        raise ExtractoNoEncontradoError(
            f"No existe extracto {cod}"
        )

    (
        _codigo_extracto,
        _provincia,
        nombre_extracto,
        p4,
        p3,
        p2,
        p1,
        aprox4,
        aprox3,
        tope_redoblona,
    ) = extracto

    aprox4 = Decimal(
        str(
            aprox4 or 100
        )
    )

    aprox3 = Decimal(
        str(
            aprox3 or 10
        )
    )

    tope_redoblona = Decimal(
        str(
            tope_redoblona or 1000
        )
    )

    calculo_repository.eliminar_premios_extracto(
        conn=conn,
        fecha=fecha,
        turno=turno_normalizado,
        codigo_extracto=cod,
    )

    resultados = (
        calculo_repository.obtener_resultados_extracto(
            conn=conn,
            fecha=fecha,
            turno=turno_normalizado,
            codigo_extracto=cod,
        )
    )

    if not resultados:
        raise ResultadosNoEncontradosError(
            "No hay resultados cargados "
            f"para fecha={fecha}, extracto={cod}"
        )

    rows = (
        calculo_repository.obtener_apuestas_extracto(
            conn=conn,
            fecha=fecha,
            turno=turno_normalizado,
            codigo_extracto=cod,
        )
    )

    apuestas = _mapear_apuestas(
        rows
    )

    apuestas = marcar_redoblonas_por_patron(
        apuestas
    )

    redoblonas_por_grupo = (
        _agrupar_redoblonas(
            apuestas
        )
    )

    for actual in apuestas:
        numero = actual[
            "c_nroapos"
        ]

        if not numero:
            continue

        if actual[
            "es_redoblona_detalle"
        ]:
            continue

        if actual[
            "es_redoblona_base"
        ]:
            grupo = actual[
                "redoblona_grupo"
            ]

            detalle = next(
                (
                    apuesta
                    for apuesta
                    in redoblonas_por_grupo.get(
                        grupo,
                        [],
                    )
                    if apuesta[
                        "es_redoblona_detalle"
                    ]
                ),
                None,
            )

            if not detalle:
                continue

            _procesar_redoblona(
                conn,
                actual=actual,
                detalle=detalle,
                resultados=resultados,
                fecha=fecha,
                codigo_extracto=cod,
                p4=p4,
                p3=p3,
                p2=p2,
                p1=p1,
                tope_redoblona=tope_redoblona,
            )

            continue

        _procesar_apuesta_normal(
            conn,
            actual=actual,
            resultados=resultados,
            fecha=fecha,
            codigo_extracto=cod,
            p4=p4,
            p3=p3,
            p2=p2,
            p1=p1,
            aprox4=aprox4,
            aprox3=aprox3,
        )

    total_normales = redondear_a_diez_centavos(
        calculo_repository.obtener_total_premios_normales(
            conn=conn,
            fecha=fecha,
            turno=turno_normalizado,
            codigo_extracto=cod,
        )
        / Decimal("100")
    )

    total_aproximaciones = redondear_a_diez_centavos(
        calculo_repository.obtener_total_aproximaciones(
            conn=conn,
            fecha=fecha,
            turno=turno_normalizado,
            codigo_extracto=cod,
        )
        / Decimal("100")
    )

    total_redoblonas = redondear_a_diez_centavos(
        calculo_repository.obtener_total_redoblonas(
            conn=conn,
            fecha=fecha,
            turno=turno_normalizado,
            codigo_extracto=cod,
        )
        / Decimal("100")
    )

    total_final = redondear_a_diez_centavos(
        total_normales
        + total_aproximaciones
        + total_redoblonas
    ).quantize(
        Decimal("0.01")
    )

    cant_premios = (
        calculo_repository.contar_apuestas_premiadas(
            conn=conn,
            fecha=fecha,
            turno=turno_normalizado,
            codigo_extracto=cod,
        )
    )

    total_recaudado = redondear_a_diez_centavos(
        calculo_repository.obtener_total_recaudado(
            conn=conn,
            fecha=fecha,
            turno=turno_normalizado,
            codigo_extracto=cod,
        )
        / Decimal("100")
    ).quantize(
        Decimal("0.01")
    )

    cupones_jugados = (
        calculo_repository.contar_cupones_jugados(
            conn=conn,
            fecha=fecha,
            turno=turno_normalizado,
            codigo_extracto=cod,
        )
    )
    """
    archivo_aciertos_dbf = (
        calculo_repository.contar_aciertos_dbf_extracto(
            conn=conn,
            fecha=fecha,
            turno=turno_normalizado,
            codigo_extracto=cod,
        )
    )
    """
    return {
        "codigo_extracto": cod,
        "sorteo": nombre_extracto,
        "cupones_jugados": cupones_jugados,
        "recaudacion": total_recaudado,
        "importe_premiados": total_final,
        "apuestas_premiadas": cant_premios,
    }


def guardar_resumen_auditoria(
    conn,
    fecha: int,
    turno: str,
    reportes: list[dict[str, Any]],
    cupones_ganadores_unicos: int,
) -> None:
    for reporte in reportes:
        calculo_repository.guardar_resumen_extracto(
            conn=conn,
            fecha=fecha,
            turno=turno,
            reporte=reporte,
            cupones_ganadores_unicos= cupones_ganadores_unicos
        )


def calcular_por_fecha_turno(
    fecha: int,
    turno: str,
) -> dict[str, Any]:
    turno_normalizado = (
        turno.upper().strip()
    )

    try:
        with transaction() as conn:
            validar_precondiciones_calculo(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
            )

            extractos = (
                calculo_repository.obtener_extractos_del_turno(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )

            if not extractos:
                raise SinExtractosParaCalcularError(
                    "No hay extractos para "
                    f"fecha={fecha}, turno={turno_normalizado}"
                )

            reportes = []

            for codigo_extracto in extractos:
                resultado = calcular_extracto(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                    cod=codigo_extracto,
                )

                reportes.append(
                    resultado
                )

            cupones_ganadores_unicos = (
                calculo_repository.contar_cupones_ganadores_unicos(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )
            """
            cupones_ganadores_dbf = (
                calculo_repository.contar_cupones_ganadores_unicos_dbf(
                    conn=conn,
                    fecha=fecha,
                    turno=turno_normalizado,
                )
            )
            """
            guardar_resumen_auditoria(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
                reportes=reportes,
                cupones_ganadores_unicos= cupones_ganadores_unicos
            )

            marcar_calculo_ejecutado(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
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
            "Error al ejecutar cálculo: "
            "fecha=%s turno=%s",
            fecha,
            turno_normalizado,
        )

        raise ErrorProcesamientoCalculo(
            "Error al ejecutar el cálculo"
        ) from error


def obtener_resumen_por_fecha(
    fecha: int,
) -> dict[str, Any]:
    try:
        with transaction() as conn:
            rows = (
                calculo_repository.obtener_resumen_por_fecha(
                    conn=conn,
                    fecha=fecha,
                )
            )

        turnos = {}

        for row in rows:
            (
                _fecha_sorteo,
                turno,
                codigo_extracto,
                sorteo,
                cupones_jugados,
                recaudacion,
                importe_premiados,
                comision,
                utilidad,
                porcentaje_utilidad,
                apuestas_premiadas,
                archivo_aciertos_dbf,
                cupones_ganadores_unicos,
                cupones_ganadores_dbf,
                fecha_calculo,
            ) = row

            if turno not in turnos:
                turnos[turno] = {
                    "turno": turno,
                    "cupones_ganadores_unicos": int(
                        cupones_ganadores_unicos
                    ),
                    "cupones_ganadores_dbf": int(
                        cupones_ganadores_dbf
                    ),
                    "fecha_calculo": str(
                        fecha_calculo
                    ),
                    "reportes": [],
                }

            turnos[turno][
                "reportes"
            ].append(
                {
                    "codigo_extracto": int(
                        codigo_extracto
                    ),
                    "sorteo": sorteo,
                    "cupones_jugados": int(
                        cupones_jugados
                    ),
                    "recaudacion": float(
                        recaudacion
                    ),
                    "importe_premiados": float(
                        importe_premiados
                    ),
                    "comision": float(
                        comision
                    ),
                    "utilidad": float(
                        utilidad
                    ),
                    "porcentaje_utilidad": float(
                        porcentaje_utilidad
                    ),
                    "apuestas_premiadas": int(
                        apuestas_premiadas
                    ),
                    "archivo_aciertos_dbf": int(
                        archivo_aciertos_dbf
                    ),
                }
            )

        return {
            "ok": True,
            "fecha": fecha,
            "origen": "resumen_auditoria",
            "turnos": list(
                turnos.values()
            ),
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error al obtener resumen de cálculo: fecha=%s",
            fecha,
        )

        raise ErrorProcesamientoCalculo(
            "Error al obtener el resumen de cálculo"
        ) from error