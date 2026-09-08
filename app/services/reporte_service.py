from decimal import Decimal
from typing import Any

from app.core.transaction import transaction
from app.repositories import reporte_repository


def _decimal_a_float(
    valor,
) -> float:
    return float(
        Decimal(
            str(valor or 0)
        )
    )


from decimal import Decimal
from typing import Any

from app.core.transaction import transaction
from app.repositories import reporte_repository


def _decimal_a_float(valor) -> float:
    return float(
        Decimal(
            str(valor or 0)
        )
    )


def obtener_control_aciertos(
    fecha: int,
    turno: str,
) -> dict[str, Any]:
    turno_normalizado = turno.upper().strip()

    with transaction() as conn:
        rows = reporte_repository.obtener_control_aciertos(
            conn=conn,
            fecha=fecha,
            turno=turno_normalizado,
        )

        cupones_unicos_dbf = (
            reporte_repository.obtener_cupones_ganadores_unicos_frontend(
                conn=conn,
                fecha=fecha,
                turno=turno_normalizado,
            )
        )

    reportes = []

    total_recaudacion = Decimal("0.00")
    total_aciertos = Decimal("0.00")
    total_importe_frontend = Decimal("0.00")
    total_comision = Decimal("0.00")
    total_utilidad = Decimal("0.00")

    total_generados_frontend = 0
    total_auditoria = 0

    cupones_unicos_sistema = None

    for row in rows:
        (
            codigo_extracto,
            sorteo,
            cupones_jugados,
            recaudacion,
            importe_premiados,
            comision,
            utilidad,
            porcentaje_utilidad,
            apuestas_premiadas,
            generados_frontend,
            importe_frontend,
            cupones_ganadores_unicos,
            cupones_ganadores_dbf_por_extracto,
        ) = row

        recaudacion = Decimal(
            str(recaudacion or 0)
        )

        importe_premiados = Decimal(
            str(importe_premiados or 0)
        )

        importe_frontend = Decimal(
            str(importe_frontend or 0)
        )

        comision = Decimal(
            str(comision or 0)
        )

        utilidad = Decimal(
            str(utilidad or 0)
        )

        total_recaudacion += recaudacion
        total_aciertos += importe_premiados
        total_importe_frontend += importe_frontend
        total_comision += comision
        total_utilidad += utilidad

        total_generados_frontend += int(
            generados_frontend or 0
        )

        total_auditoria += int(
            apuestas_premiadas or 0
        )

        if cupones_unicos_sistema is None:
            cupones_unicos_sistema = int(
                cupones_ganadores_unicos or 0
            )

        reportes.append(
            {
                "codigo_extracto": int(
                    codigo_extracto
                ),
                "sorteo": sorteo,
                "cupones_jugados": int(
                    cupones_jugados or 0
                ),
                "recaudacion": _decimal_a_float(
                    recaudacion
                ),
                "importe_aciertos": _decimal_a_float(
                    importe_premiados
                ),
                "importe_frontend": _decimal_a_float(
                    importe_frontend
                ),
                "comision": _decimal_a_float(
                    comision
                ),
                "utilidad": _decimal_a_float(
                    utilidad
                ),
                "porcentaje_utilidad": _decimal_a_float(
                    porcentaje_utilidad
                ),
                "generados_frontend": int(
                    generados_frontend or 0
                ),
                "generados_auditoria": int(
                    apuestas_premiadas or 0
                ),
            }
        )

    return {
        "ok": True,
        "fecha": fecha,
        "turno": turno_normalizado,
        "reportes": reportes,
        "totales": {
            "recaudacion": _decimal_a_float(
                total_recaudacion
            ),
            "importe_aciertos": _decimal_a_float(
                total_aciertos
            ),
            "importe_frontend": _decimal_a_float(
                total_importe_frontend
            ),
            "comision": _decimal_a_float(
                total_comision
            ),
            "utilidad": _decimal_a_float(
                total_utilidad
            ),
            "generados_frontend": total_generados_frontend,
            "generados_auditoria": total_auditoria,
        },
        "cupones_ganadores_unicos": {
            "frontend": int(
                cupones_unicos_dbf or 0
            ),
            "auditoria": int(
                cupones_unicos_sistema or 0
            ),
        },
    }

