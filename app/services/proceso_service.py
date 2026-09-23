from decimal import Decimal

from app.database import get_connection
from app.repositories.proceso_repository import (
    obtener_apuestas_jornada,
    obtener_cupones_jugados_unicos_jornada,
    obtener_cupones_jugados_unicos_por_turno,
    obtener_cupones_premiados_dbf,
    obtener_cupones_unicos_auditoria_por_turno,
    obtener_cupones_unicos_dbf_por_turno,
    obtener_estados_jornada,
    obtener_importes_dbf_por_turno,
    obtener_resultados_auditoria,
)


# =========================================================
# CONFIGURACIÓN DE TURNOS
# =========================================================

NOMBRES_EVENTOS = {
    "PV": "LA PREVIA",
    "PR": "PRIMERA",
    "M": "MATUTINA",
    "V": "VESPERTINA",
    "N": "NOCTURNA",
}


ORDEN_TURNOS = {
    "PV": 1,
    "PR": 2,
    "M": 3,
    "V": 4,
    "N": 5,
}


# =========================================================
# HELPERS
# =========================================================

def _decimal(valor) -> Decimal:
    """
    Convierte un valor numérico a Decimal de forma segura.
    """

    if valor is None:
        return Decimal("0")

    return Decimal(str(valor))


def _float(valor) -> float:
    """
    Convierte Decimal/número a float para la respuesta JSON.
    """

    return float(_decimal(valor))


def _int(valor) -> int:
    """
    Convierte un valor a int de forma segura.
    """

    if valor is None:
        return 0

    return int(valor)


# =========================================================
# SERVICIO PRINCIPAL
# =========================================================

def obtener_estado_proceso(
    fecha: int,
) -> dict:
    """
    Obtiene toda la información necesaria para representar
    la pantalla "Proceso de Quiniela".

    La respuesta contiene:

    - resumen por evento/turno
    - filas por extracto
    - estados del proceso
    - recaudación
    - cupones jugados
    - importes calculados por Auditoría
    - importes informados por DBF
    - cupones premiados por Auditoría
    - cupones premiados informados por DBF
    - totales generales de la jornada
    """

    with get_connection() as conn:

        # -------------------------------------------------
        # DATOS BASE DE LA JORNADA
        # -------------------------------------------------

        apuestas_jornada = obtener_apuestas_jornada(
            conn,
            fecha,
        )

        estados_jornada = obtener_estados_jornada(
            conn,
            fecha,
        )

        resultados_auditoria = obtener_resultados_auditoria(
            conn,
            fecha,
        )

        cupones_premiados_dbf = obtener_cupones_premiados_dbf(
            conn,
            fecha,
        )

        # -------------------------------------------------
        # TOTALES POR TURNO
        # -------------------------------------------------

        cupones_unicos_auditoria = (
            obtener_cupones_unicos_auditoria_por_turno(
                conn,
                fecha,
            )
        )

        cupones_unicos_dbf = (
            obtener_cupones_unicos_dbf_por_turno(
                conn,
                fecha,
            )
        )

        importes_dbf = obtener_importes_dbf_por_turno(
            conn,
            fecha,
        )

        # -------------------------------------------------
        # CUPONES JUGADOS ÚNICOS
        # -------------------------------------------------

        cupones_jugados_por_turno = (
            obtener_cupones_jugados_unicos_por_turno(
                conn,
                fecha,
            )
        )

        cupones_jugados_jornada = (
            obtener_cupones_jugados_unicos_jornada(
                conn,
                fecha,
            )
        )

    # =====================================================
    # ÍNDICES PARA ACCESO RÁPIDO
    # =====================================================

    estados_map = {
        item["turno"]: item
        for item in estados_jornada
    }

    auditoria_map = {
        (
            item["turno"],
            item["codigo_extracto"],
        ): item
        for item in resultados_auditoria
    }

    dbf_extracto_map = {
        (
            item["turno"],
            item["codigo_extracto"],
        ): item
        for item in cupones_premiados_dbf
    }

    cupones_auditoria_turno_map = {
        item["turno"]: _int(item["cupones"])
        for item in cupones_unicos_auditoria
    }

    cupones_dbf_turno_map = {
        item["turno"]: _int(item["cupones"])
        for item in cupones_unicos_dbf
    }

    importes_dbf_turno_map = {
        item["turno"]: _decimal(
            item["importe_aciertos_sistema"]
        )
        for item in importes_dbf
    }

    cupones_jugados_turno_map = {
        item["turno"]: _int(
            item["cupones_jugados"]
        )
        for item in cupones_jugados_por_turno
    }

    # =====================================================
    # CONSTRUCCIÓN DE FILAS
    # =====================================================

    filas = []

    for apuesta in apuestas_jornada:

        turno = apuesta["turno"]
        codigo_extracto = apuesta["codigo_extracto"]

        estado = estados_map.get(
            turno,
            {},
        )

        auditoria = auditoria_map.get(
            (
                turno,
                codigo_extracto,
            ),
            {},
        )

        dbf = dbf_extracto_map.get(
            (
                turno,
                codigo_extracto,
            ),
            {},
        )

        extracto = (
            apuesta.get("extracto")
            or auditoria.get("extracto")
            or f"Extracto {codigo_extracto}"
        )

        fila = {
            "turno": turno,
            "evento": NOMBRES_EVENTOS.get(
                turno,
                turno,
            ),
            "codigo_extracto": codigo_extracto,
            "extracto": extracto,

            # ---------------------------------------------
            # ESTADOS DEL PROCESO
            # ---------------------------------------------

            "exp_cargado": bool(
                estado.get(
                    "exp_cargado",
                    False,
                )
            ),

            "resultados_cargados": bool(
                estado.get(
                    "resultados_cargados",
                    False,
                )
            ),

            "calculo_ejecutado": bool(
                estado.get(
                    "calculo_ejecutado",
                    False,
                )
            ),

            "dbf_cargado": bool(
                estado.get(
                    "dbf_cargado",
                    False,
                )
            ),

            "comparacion_ejecutada": bool(
                estado.get(
                    "comparacion_ejecutada",
                    False,
                )
            ),

            "evento_cerrado": bool(
                estado.get(
                    "evento_cerrado",
                    False,
                )
            ),

            # ---------------------------------------------
            # DATOS ECONÓMICOS / OPERATIVOS
            # ---------------------------------------------

            "recaudacion": _float(
                apuesta.get(
                    "recaudacion",
                    0,
                )
            ),

            "cupones_jugados": _int(
                apuesta.get(
                    "cupones_jugados",
                    0,
                )
            ),

            "importe_aciertos": _float(
                auditoria.get(
                    "importe_aciertos",
                    0,
                )
            ),

            "cupones_premiados": _int(
                auditoria.get(
                    "cupones_premiados",
                    0,
                )
            ),

            "cupones_premiados_sistema": _int(
                dbf.get(
                    "cupones_premiados_sistema",
                    0,
                )
            ),
        }

        filas.append(fila)

    # =====================================================
    # ORDENAR FILAS
    # =====================================================

    filas.sort(
        key=lambda fila: (
            ORDEN_TURNOS.get(
                fila["turno"],
                99,
            ),
            fila["codigo_extracto"],
        )
    )

    # =====================================================
    # RESUMEN POR EVENTO
    # =====================================================

    resumen_eventos = []

    turnos_presentes = []

    for fila in filas:
        turno = fila["turno"]

        if turno not in turnos_presentes:
            turnos_presentes.append(turno)

    turnos_presentes.sort(
        key=lambda turno: ORDEN_TURNOS.get(
            turno,
            99,
        )
    )

    for turno in turnos_presentes:

        filas_turno = [
            fila
            for fila in filas
            if fila["turno"] == turno
        ]

        importe_recaudacion = sum(
            (
                _decimal(
                    fila["recaudacion"]
                )
                for fila in filas_turno
            ),
            Decimal("0"),
        )

        importe_aciertos_auditoria = sum(
            (
                _decimal(
                    fila["importe_aciertos"]
                )
                for fila in filas_turno
            ),
            Decimal("0"),
        )

        resumen_eventos.append(
            {
                "turno": turno,

                "evento": NOMBRES_EVENTOS.get(
                    turno,
                    turno,
                ),

                "importe_recaudacion": float(
                    importe_recaudacion
                ),

                # IMPORTANTE:
                # Ya no sumamos los cupones de los 7 extractos.
                # Se cuentan los cupones únicos del turno.
                "total_cupones_jugados": (
                    cupones_jugados_turno_map.get(
                        turno,
                        0,
                    )
                ),

                "importe_aciertos_auditoria": float(
                    importe_aciertos_auditoria
                ),

                "importe_aciertos_sistema": float(
                    importes_dbf_turno_map.get(
                        turno,
                        Decimal("0"),
                    )
                ),

                "cupones_aciertos_auditoria": (
                    cupones_auditoria_turno_map.get(
                        turno,
                        0,
                    )
                ),

                "cupones_aciertos_sistema": (
                    cupones_dbf_turno_map.get(
                        turno,
                        0,
                    )
                ),
            }
        )

    # =====================================================
    # TOTALES DE LA JORNADA
    # =====================================================

    total_recaudacion = sum(
        (
            _decimal(
                fila["recaudacion"]
            )
            for fila in filas
        ),
        Decimal("0"),
    )

    total_importe_aciertos = sum(
        (
            _decimal(
                fila["importe_aciertos"]
            )
            for fila in filas
        ),
        Decimal("0"),
    )

    total_cupones_con_aciertos = sum(
        cupones_auditoria_turno_map.get(
            turno,
            0,
        )
        for turno in turnos_presentes
    )

    # =====================================================
    # RESPUESTA
    # =====================================================

    return {
        "ok": True,
        "fecha": fecha,

        "resumen_eventos": resumen_eventos,

        "filas": filas,

        "totales": {
            "recaudacion": float(
                total_recaudacion
            ),

            # Cupones únicos considerando:
            # turno + agencia + subagencia + máquina + cupón
            "cupones_jugados": _int(
                cupones_jugados_jornada
            ),

            "importe_aciertos": float(
                total_importe_aciertos
            ),

            "cupones_con_aciertos": (
                total_cupones_con_aciertos
            ),
        },
    }