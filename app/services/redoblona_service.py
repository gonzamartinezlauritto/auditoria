from decimal import Decimal, ROUND_HALF_UP

from app.services.premios_service import (
    cantidad_puestos,
)


def ajustar_rango_detalle_redoblona(
    base_desde,
    base_hasta,
    det_desde,
    det_hasta,
) -> tuple[int, int]:
    base_desde = int(
        base_desde or 0
    )

    base_hasta = int(
        base_hasta or 0
    )

    det_desde = int(
        det_desde or 0
    )

    det_hasta = int(
        det_hasta or 0
    )

    if (
        base_desde == 0
        and base_hasta == 1
    ):
        return (
            2,
            min(
                det_hasta + 1,
                20,
            ),
        )

    return (
        det_desde,
        det_hasta,
    )


def calcular_tope_redoblona(
    importe,
    desde,
    hasta,
    tope_redoblona,
) -> Decimal:
    puestos = cantidad_puestos(
        desde,
        hasta,
    )

    if puestos <= 0:
        return Decimal("0.00")

    return (
        Decimal(str(importe))
        * Decimal(
            str(tope_redoblona)
        )
        / Decimal(puestos)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def marcar_redoblonas_por_patron(
    apuestas: list[dict],
) -> list[dict]:
    apuestas = sorted(
        apuestas,
        key=lambda apuesta: (
            apuesta["n_agent"],
            apuesta["n_subag"],
            apuesta["n_maqui"],
            apuesta["n_cupon"],
            apuesta["n_codext"],
            apuesta["n_linea"],
            apuesta["id"],
        ),
    )

    grupo = 1
    indice = 0

    while indice < len(apuestas) - 1:
        actual = apuestas[indice]
        siguiente = apuestas[
            indice + 1
        ]

        misma_apuesta = (
            actual["n_agent"]
            == siguiente["n_agent"]
            and actual["n_subag"]
            == siguiente["n_subag"]
            and actual["n_maqui"]
            == siguiente["n_maqui"]
            and actual["n_cupon"]
            == siguiente["n_cupon"]
            and actual["n_codext"]
            == siguiente["n_codext"]
        )

        lineas_consecutivas = (
            int(
                siguiente["n_linea"]
            )
            == int(
                actual["n_linea"]
            )
            + 1
        )

        misma_cantidad_cifras = (
            len(
                actual["c_nroapos"]
            ) > 0
            and len(
                actual["c_nroapos"]
            )
            == len(
                siguiente["c_nroapos"]
            )
        )

        es_patron_redoblona = (
            misma_apuesta
            and lineas_consecutivas
            and misma_cantidad_cifras
            and actual["n_impapos"]
            > Decimal("0.00")
            and siguiente["n_impapos"]
            == Decimal("0.00")
        )

        if es_patron_redoblona:
            actual[
                "es_redoblona_base"
            ] = True

            actual[
                "es_redoblona_detalle"
            ] = False

            actual[
                "redoblona_grupo"
            ] = grupo

            siguiente[
                "es_redoblona_base"
            ] = False

            siguiente[
                "es_redoblona_detalle"
            ] = True

            siguiente[
                "redoblona_grupo"
            ] = grupo

            grupo += 1
            indice += 2

        else:
            indice += 1

    return apuestas