from decimal import Decimal

from app.services.redoblona_service import (
    ajustar_rango_detalle_redoblona,
    calcular_tope_redoblona,
    marcar_redoblonas_por_patron,
)


def test_ajustar_rango_detalle_base_cabeza_0_5():
    desde, hasta = ajustar_rango_detalle_redoblona(
        base_desde=0,
        base_hasta=1,
        det_desde=0,
        det_hasta=5,
    )

    assert desde == 2
    assert hasta == 6


def test_ajustar_rango_detalle_base_cabeza_0_10():
    desde, hasta = ajustar_rango_detalle_redoblona(
        base_desde=0,
        base_hasta=1,
        det_desde=0,
        det_hasta=10,
    )

    assert desde == 2
    assert hasta == 11


def test_ajustar_rango_detalle_no_supera_20():
    desde, hasta = ajustar_rango_detalle_redoblona(
        base_desde=0,
        base_hasta=1,
        det_desde=0,
        det_hasta=20,
    )

    assert desde == 2
    assert hasta == 20


def test_ajustar_rango_detalle_sin_desplazamiento():
    desde, hasta = ajustar_rango_detalle_redoblona(
        base_desde=0,
        base_hasta=10,
        det_desde=0,
        det_hasta=10,
    )

    assert desde == 0
    assert hasta == 10


def test_calcular_tope_redoblona():
    resultado = calcular_tope_redoblona(
        importe=100,
        desde=0,
        hasta=10,
        tope_redoblona=1000,
    )

    assert resultado == Decimal("10000.00")


def test_calcular_tope_redoblona_a_cabeza():
    resultado = calcular_tope_redoblona(
        importe=100,
        desde=0,
        hasta=1,
        tope_redoblona=1000,
    )

    assert resultado == Decimal("100000.00")


def test_marcar_redoblona_por_patron():
    apuestas = [
        {
            "id": 1,
            "n_agent": 10,
            "n_subag": 1,
            "n_maqui": 1,
            "n_cupon": 100,
            "n_codext": 50,
            "n_linea": 1,
            "c_nroapos": "19",
            "n_impapos": Decimal("100.00"),
            "es_redoblona_base": False,
            "es_redoblona_detalle": False,
            "redoblona_grupo": None,
        },
        {
            "id": 2,
            "n_agent": 10,
            "n_subag": 1,
            "n_maqui": 1,
            "n_cupon": 100,
            "n_codext": 50,
            "n_linea": 2,
            "c_nroapos": "32",
            "n_impapos": Decimal("0.00"),
            "es_redoblona_base": False,
            "es_redoblona_detalle": False,
            "redoblona_grupo": None,
        },
    ]

    resultado = marcar_redoblonas_por_patron(
        apuestas
    )

    assert resultado[0]["es_redoblona_base"] is True
    assert resultado[0]["es_redoblona_detalle"] is False
    assert resultado[0]["redoblona_grupo"] == 1

    assert resultado[1]["es_redoblona_base"] is False
    assert resultado[1]["es_redoblona_detalle"] is True
    assert resultado[1]["redoblona_grupo"] == 1


def test_no_marcar_redoblona_si_lineas_no_consecutivas():
    apuestas = [
        {
            "id": 1,
            "n_agent": 10,
            "n_subag": 1,
            "n_maqui": 1,
            "n_cupon": 100,
            "n_codext": 50,
            "n_linea": 1,
            "c_nroapos": "19",
            "n_impapos": Decimal("100.00"),
            "es_redoblona_base": False,
            "es_redoblona_detalle": False,
            "redoblona_grupo": None,
        },
        {
            "id": 2,
            "n_agent": 10,
            "n_subag": 1,
            "n_maqui": 1,
            "n_cupon": 100,
            "n_codext": 50,
            "n_linea": 3,
            "c_nroapos": "32",
            "n_impapos": Decimal("0.00"),
            "es_redoblona_base": False,
            "es_redoblona_detalle": False,
            "redoblona_grupo": None,
        },
    ]

    resultado = marcar_redoblonas_por_patron(
        apuestas
    )

    assert resultado[0]["es_redoblona_base"] is False
    assert resultado[1]["es_redoblona_detalle"] is False