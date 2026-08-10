from decimal import Decimal, ROUND_HALF_UP


def redondear_a_diez_centavos(
    valor,
) -> Decimal:
    valor = Decimal(
        str(valor or 0)
    )

    return (
        (
            valor
            / Decimal("0.10")
        )
        .quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
        * Decimal("0.10")
    ).quantize(
        Decimal("0.01")
    )


def limpiar_numero(
    numero,
) -> str:
    return str(
        numero or ""
    ).strip()


def normalizar_resultado(
    numero,
) -> str:
    return str(
        numero or ""
    ).strip().zfill(4)


def coincide(
    numero_apostado,
    numero_resultado,
) -> int:
    apuesta = limpiar_numero(
        numero_apostado
    )

    resultado = normalizar_resultado(
        numero_resultado
    )

    if (
        len(apuesta) == 4
        and apuesta == resultado
    ):
        return 4

    if (
        len(apuesta) == 3
        and apuesta == resultado[-3:]
    ):
        return 3

    if (
        len(apuesta) == 2
        and apuesta == resultado[-2:]
    ):
        return 2

    if (
        len(apuesta) == 1
        and apuesta == resultado[-1:]
    ):
        return 1

    return 0


def puesto_en_rango(
    orden,
    desde,
    hasta,
) -> bool:
    desde = int(
        desde or 0
    )

    hasta = int(
        hasta or 0
    )

    if hasta <= 0:
        return False

    if desde == 0:
        return (
            1
            <= orden
            <= hasta
        )

    return (
        desde
        <= orden
        <= hasta
    )


def cantidad_puestos(
    desde,
    hasta,
) -> int:
    desde = int(
        desde or 0
    )

    hasta = int(
        hasta or 0
    )

    if hasta <= 0:
        return 0

    if desde == 0:
        return hasta

    return (
        hasta
        - desde
        + 1
    )


def obtener_multiplicador(
    cifras,
    p4,
    p3,
    p2,
    p1,
) -> Decimal:
    return {
        4: Decimal(str(p4)),
        3: Decimal(str(p3)),
        2: Decimal(str(p2)),
        1: Decimal(str(p1)),
    }.get(
        cifras,
        Decimal("0"),
    )


def calcular_premio(
    importe,
    multiplicador,
    puestos,
) -> Decimal:
    if puestos <= 0:
        return Decimal("0.00")

    return (
        Decimal(str(importe))
        * Decimal(str(multiplicador))
        / Decimal(puestos)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def formatear(
    valor,
) -> str:
    valor = Decimal(
        str(valor or 0)
    ).quantize(
        Decimal("0.01")
    )

    return (
        f"{valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def obtener_hits(
    numero,
    desde,
    hasta,
    resultados,
) -> list[tuple]:
    hits = []

    for orden, resultado in resultados:
        if not puesto_en_rango(
            orden,
            desde,
            hasta,
        ):
            continue

        cifras = coincide(
            numero,
            resultado,
        )

        if cifras:
            hits.append(
                (
                    orden,
                    resultado,
                    cifras,
                )
            )

    return hits


def es_a_la_cabeza(
    desde,
    hasta,
) -> bool:
    return (
        int(desde or 0) == 0
        and int(hasta or 0) == 1
    )


def numero_anterior(
    valor,
    ancho,
) -> str | None:
    numero = int(valor)

    if numero == 0:
        return None

    return str(
        numero - 1
    ).zfill(
        ancho
    )


def numero_siguiente(
    valor,
    ancho,
) -> str | None:
    numero = int(valor)

    if numero == (
        10 ** ancho
    ) - 1:
        return None

    return str(
        numero + 1
    ).zfill(
        ancho
    )


def buscar_aproximado(
    numero,
    resultados,
    aprox4,
    aprox3,
):
    if not resultados:
        return None

    orden, primero = resultados[0]

    primero = normalizar_resultado(
        primero
    )

    apuesta = limpiar_numero(
        numero
    )

    if len(apuesta) == 4:
        if apuesta in (
            numero_anterior(
                primero,
                4,
            ),
            numero_siguiente(
                primero,
                4,
            ),
        ):
            return (
                "aprox_4",
                orden,
                primero,
                4,
                Decimal(
                    str(aprox4)
                ),
            )

    if len(apuesta) == 3:
        cola = primero[-3:]

        if apuesta in (
            numero_anterior(
                cola,
                3,
            ),
            numero_siguiente(
                cola,
                3,
            ),
        ):
            return (
                "aprox_3",
                orden,
                primero,
                3,
                Decimal(
                    str(aprox3)
                ),
            )

    return None