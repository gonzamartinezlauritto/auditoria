from decimal import Decimal

from app.services.premios_service import (
    buscar_aproximado,
    calcular_premio,
    cantidad_puestos,
    coincide,
    es_a_la_cabeza,
    numero_anterior,
    numero_siguiente,
    obtener_hits,
    obtener_multiplicador,
    puesto_en_rango,
    redondear_a_diez_centavos,
)


def test_coincide_4_cifras():
    assert coincide("0731", "0731") == 4


def test_coincide_3_cifras():
    assert coincide("731", "0731") == 3


def test_coincide_2_cifras():
    assert coincide("31", "0731") == 2


def test_coincide_1_cifra():
    assert coincide("1", "0731") == 1


def test_no_coincide():
    assert coincide("99", "0731") == 0


def test_puesto_en_rango_desde_cero():
    assert puesto_en_rango(
        orden=1,
        desde=0,
        hasta=10,
    )


def test_puesto_fuera_de_rango():
    assert not puesto_en_rango(
        orden=11,
        desde=0,
        hasta=10,
    )


def test_cantidad_puestos_0_10():
    assert cantidad_puestos(
        desde=0,
        hasta=10,
    ) == 10


def test_cantidad_puestos_2_6():
    assert cantidad_puestos(
        desde=2,
        hasta=6,
    ) == 5


def test_multiplicador_4_cifras():
    resultado = obtener_multiplicador(
        cifras=4,
        p4=3500,
        p3=600,
        p2=70,
        p1=5,
    )

    assert resultado == Decimal("3500")


def test_calcular_premio_divide_por_puestos():
    resultado = calcular_premio(
        importe=100,
        multiplicador=70,
        puestos=10,
    )

    assert resultado == Decimal("700.00")


def test_redondear_a_diez_centavos():
    assert redondear_a_diez_centavos(
        Decimal("10.06")
    ) == Decimal("10.10")

    assert redondear_a_diez_centavos(
        Decimal("10.04")
    ) == Decimal("10.00")


def test_es_a_la_cabeza():
    assert es_a_la_cabeza(
        desde=0,
        hasta=1,
    )


def test_no_es_a_la_cabeza():
    assert not es_a_la_cabeza(
        desde=0,
        hasta=10,
    )


def test_numero_anterior():
    assert numero_anterior(
        "0731",
        4,
    ) == "0730"


def test_numero_anterior_cero():
    assert numero_anterior(
        "0000",
        4,
    ) is None


def test_numero_siguiente():
    assert numero_siguiente(
        "0731",
        4,
    ) == "0732"


def test_numero_siguiente_maximo():
    assert numero_siguiente(
        "9999",
        4,
    ) is None


def test_obtener_hits_con_numero_repetido():
    resultados = [
        (1, "1266"),
        (2, "7866"),
        (3, "1234"),
    ]

    hits = obtener_hits(
        numero="66",
        desde=0,
        hasta=10,
        resultados=resultados,
    )

    assert len(hits) == 2
    assert hits[0][0] == 1
    assert hits[1][0] == 2


def test_buscar_aproximado_4_cifras_anterior():
    resultados = [
        (1, "0731"),
    ]

    resultado = buscar_aproximado(
        numero="0730",
        resultados=resultados,
        aprox4=100,
        aprox3=10,
    )

    assert resultado is not None

    tipo, orden, numero_resultado, cifras, multiplicador = (
        resultado
    )

    assert tipo == "aprox_4"
    assert orden == 1
    assert numero_resultado == "0731"
    assert cifras == 4
    assert multiplicador == Decimal("100")


def test_buscar_aproximado_3_cifras_siguiente():
    resultados = [
        (1, "0731"),
    ]

    resultado = buscar_aproximado(
        numero="732",
        resultados=resultados,
        aprox4=100,
        aprox3=10,
    )

    assert resultado is not None
    assert resultado[0] == "aprox_3"
    assert resultado[4] == Decimal("10")