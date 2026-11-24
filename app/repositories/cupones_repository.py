
from decimal import Decimal

from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


def obtener_cupones(
    conn: connection,
    fecha_desde: int,
    fecha_hasta: int,
    turno: str | None = None,
    pagina: int = 1,
    limite: int = 20,
    agencia: int | None = None,
    subagencia: int | None = None,
    maquina: int | None = None,
    numero_cupon: int | None = None,
    codigo_extracto: int | None = None,
    solo_ganadores: bool = False,
    anulados: bool = False,
) -> dict:

    # --------------------------------------------------
    # 1. VALIDACIONES
    # --------------------------------------------------

    if pagina < 1:
        raise ValueError(
            "La página debe ser mayor o igual a 1"
        )

    if limite < 1 or limite > 100:
        raise ValueError(
            "El límite debe estar entre 1 y 100"
        )

    # La interpretación de anulados todavía
    # debe confirmarse con la base de datos.
    if anulados:
        raise ValueError(
            "La consulta de anulados todavía no está implementada"
        )

    # --------------------------------------------------
    # 2. CONDICIONES DINÁMICAS
    # --------------------------------------------------

    condiciones = [
        "q.n_fsorteo BETWEEN %(fecha_desde)s AND %(fecha_hasta)s",
        "q.c_ecupon = 'N'",
        "COALESCE(q.n_nodef, 0) <> 1",
    ]

    parametros = {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "limite_consulta": limite + 1,
        "offset": (pagina - 1) * limite,
    }

    if turno is not None:
        condiciones.append(
            "q.c_tsorteo = %(turno)s"
        )
        parametros["turno"] = turno

    filtros = {
        "n_agent": ("agencia", agencia),
        "n_subag": ("subagencia", subagencia),
        "n_maqui": ("maquina", maquina),
        "n_cupon": ("numero_cupon", numero_cupon),
        "n_codext": ("codigo_extracto", codigo_extracto),
    }

    for columna, (nombre, valor) in filtros.items():
        if valor is not None:
            condiciones.append(
                f"q.{columna} = %({nombre})s"
            )
            parametros[nombre] = valor

    where_sql = " AND ".join(condiciones)

    # --------------------------------------------------
    # 3. CONSULTA BASE
    # --------------------------------------------------

    consulta_base = f"""
        SELECT
            q.n_fsorteo AS fecha_sorteo,
            TRIM(q.c_tsorteo) AS turno,
            q.n_apues,
            q.n_codext AS codigo_extracto,
            MIN(q.n_agent) AS agencia,
            MIN(q.n_subag) AS subagencia,
            MIN(q.n_maqui) AS maquina,
            MIN(q.n_cupon) AS numero_cupon,
            COUNT(*) AS cantidad_lineas,
            SUM(q.n_impapos) / 100 AS importe_apostado
        FROM quiniela_exp q
        WHERE {where_sql}
        GROUP BY
            q.n_fsorteo,
            q.c_tsorteo,
            q.n_apues,
            q.n_codext
    """

    orden_sql = """
        ORDER BY
            fecha_sorteo,
            turno,
            agencia,
            subagencia,
            maquina,
            numero_cupon,
            codigo_extracto,
            n_apues
    """

    # --------------------------------------------------
    # 4. CONSULTA PAGINADA
    # --------------------------------------------------

    if solo_ganadores:

        consulta_ganadores = f"""
            SELECT DISTINCT
                q.n_fsorteo,
                q.c_tsorteo,
                q.n_apues,
                q.n_codext
            FROM quiniela_exp q
            WHERE {where_sql}
              AND EXISTS (
                  SELECT 1
                  FROM premios p
                  WHERE p.quiniela_exp_id = q.id
                    AND p.fecha_sorteo = q.n_fsorteo
                    AND p.codigo_extracto = q.n_codext
                    AND p.premio_total > 0
              )
        """

        consulta_paginada = f"""
            SELECT cupones.*
            FROM ({consulta_base}) cupones
            INNER JOIN ({consulta_ganadores}) ganadores
                ON ganadores.n_fsorteo = cupones.fecha_sorteo
               AND TRIM(ganadores.c_tsorteo) = cupones.turno
               AND ganadores.n_apues = cupones.n_apues
               AND ganadores.n_codext = cupones.codigo_extracto
            {orden_sql}
            LIMIT %(limite_consulta)s
            OFFSET %(offset)s
        """

    else:

        consulta_paginada = f"""
            SELECT *
            FROM ({consulta_base}) cupones
            {orden_sql}
            LIMIT %(limite_consulta)s
            OFFSET %(offset)s
        """

    # --------------------------------------------------
    # 5. EJECUCIÓN CONTROLADA
    # --------------------------------------------------

    # Máximo de 30 segundos por sentencia SQL.
    # SET LOCAL se aplica durante esta transacción.

    with conn.cursor() as cur:
        cur.execute(
            "SET LOCAL statement_timeout = '30s'"
        )

    with conn.cursor(
        cursor_factory=RealDictCursor
    ) as cur:

        cur.execute(
            consulta_paginada,
            parametros
        )

        registros = [
            dict(fila)
            for fila in cur.fetchall()
        ]

    # Consultamos un registro adicional para saber
    # si existe una página siguiente.

    hay_mas = len(registros) > limite

    # Devolvemos únicamente la cantidad solicitada.
    registros = registros[:limite]

    # --------------------------------------------------
    # 6. INICIALIZAR PREMIOS
    # --------------------------------------------------

    for registro in registros:
        registro["tiene_premio"] = False
        registro["cantidad_premios"] = 0
        registro["importe_premiado"] = 0.0

    # --------------------------------------------------
    # 7. CONSULTAR PREMIOS DE LA PÁGINA
    # --------------------------------------------------

    if registros:

        valores = []

        parametros_premios = {
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
        }

        for indice, registro in enumerate(registros):

            clave_fecha = f"fecha_{indice}"
            clave_turno = f"turno_{indice}"
            clave_apuesta = f"apuesta_{indice}"
            clave_extracto = f"extracto_{indice}"

            parametros_premios[clave_fecha] = (
                registro["fecha_sorteo"]
            )
            parametros_premios[clave_turno] = (
                registro["turno"]
            )
            parametros_premios[clave_apuesta] = (
                registro["n_apues"]
            )
            parametros_premios[clave_extracto] = (
                registro["codigo_extracto"]
            )

            valores.append(
                f"""(
                    %({clave_fecha})s,
                    %({clave_turno})s,
                    %({clave_apuesta})s,
                    %({clave_extracto})s
                )"""
            )

        valores_sql = ", ".join(valores)

        consulta_premios = f"""
            WITH cupones_pagina (
                fecha_sorteo,
                turno,
                n_apues,
                codigo_extracto
            ) AS (
                VALUES {valores_sql}
            )
            SELECT
                q.n_fsorteo AS fecha_sorteo,
                TRIM(q.c_tsorteo) AS turno,
                q.n_apues,
                q.n_codext AS codigo_extracto,
                COUNT(p.id) AS cantidad_premios,
                COALESCE(
                    SUM(p.premio_total),
                    0
                ) / 100 AS importe_premiado
            FROM cupones_pagina cp
            INNER JOIN quiniela_exp q
                ON q.n_fsorteo = cp.fecha_sorteo
               AND q.c_tsorteo = cp.turno
               AND q.n_apues = cp.n_apues
               AND q.n_codext = cp.codigo_extracto
            INNER JOIN premios p
                ON p.quiniela_exp_id = q.id
               AND p.fecha_sorteo = q.n_fsorteo
               AND p.codigo_extracto = q.n_codext
            WHERE q.n_fsorteo BETWEEN
                    %(fecha_desde)s AND %(fecha_hasta)s
              AND q.c_ecupon = 'N'
              AND COALESCE(q.n_nodef, 0) <> 1
              AND p.premio_total > 0
            GROUP BY
                q.n_fsorteo,
                q.c_tsorteo,
                q.n_apues,
                q.n_codext
        """

        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:

            cur.execute(
                consulta_premios,
                parametros_premios
            )

            premios = [
                dict(fila)
                for fila in cur.fetchall()
            ]

        premios_por_cupon = {
            (
                premio["fecha_sorteo"],
                premio["turno"],
                premio["n_apues"],
                premio["codigo_extracto"],
            ): premio
            for premio in premios
        }

        for registro in registros:

            clave = (
                registro["fecha_sorteo"],
                registro["turno"],
                registro["n_apues"],
                registro["codigo_extracto"],
            )

            premio = premios_por_cupon.get(clave)

            if premio is not None:

                registro["tiene_premio"] = True

                registro["cantidad_premios"] = (
                    premio["cantidad_premios"]
                )

                registro["importe_premiado"] = float(
                    premio["importe_premiado"]
                )

    # --------------------------------------------------
    # 8. CONVERSIÓN PARA JSON
    # --------------------------------------------------

    for registro in registros:

        if isinstance(
            registro["importe_apostado"],
            Decimal
        ):
            registro["importe_apostado"] = float(
                registro["importe_apostado"]
            )

    # --------------------------------------------------
    # 9. RESPUESTA
    # --------------------------------------------------

    return {
        "pagina": pagina,
        "limite": limite,
        "hay_mas": hay_mas,
        "cupones": registros,
    }
