from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


# =========================================================
# APUESTAS DE TODA LA JORNADA
# =========================================================

def obtener_apuestas_jornada(
    conn: connection,
    fecha: int,
) -> list[dict]:
    """
    Obtiene todos los extractos presentes en quiniela_exp
    para una fecha determinada.

    Devuelve por turno + extracto:
    - turno
    - código de extracto
    - nombre del extracto
    - recaudación
    - cupones jugados

    Los importes de quiniela_exp están almacenados x100,
    por lo que la recaudación se divide por 100.
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                TRIM(q.c_tsorteo) AS turno,
                q.n_codext AS codigo_extracto,
                e.nombre_extracto AS extracto,

                COALESCE(
                    SUM(q.n_impapos),
                    0
                ) / 100.0 AS recaudacion,

                COUNT(
                    DISTINCT (
                        q.n_agent,
                        q.n_subag,
                        q.n_maqui,
                        q.n_cupon
                    )
                ) AS cupones_jugados

            FROM quiniela_exp q

            LEFT JOIN extractos e
                ON e.codigo_extracto = q.n_codext

            WHERE q.n_fsorteo = %s
              AND COALESCE(q.c_ecupon, '') = 'N'
              AND COALESCE(q.n_nodef, 0) <> 1
              AND q.n_impapos > 0

            GROUP BY
                TRIM(q.c_tsorteo),
                q.n_codext,
                e.nombre_extracto

            ORDER BY
                CASE TRIM(q.c_tsorteo)
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M'  THEN 3
                    WHEN 'V'  THEN 4
                    WHEN 'N'  THEN 5
                    ELSE 99
                END,
                q.n_codext
            """,
            (fecha,),
        )

        return cur.fetchall()


# =========================================================
# ESTADOS DE LOS EVENTOS
# =========================================================

def obtener_estados_jornada(
    conn: connection,
    fecha: int,
) -> list[dict]:
    """
    Obtiene los estados de procesamiento de cada turno
    desde auditoria_cargas.

    Un turno puede tener apuestas en quiniela_exp y todavía
    no existir en auditoria_cargas. En ese caso el service
    completará sus estados como False.

    hay_diferencias:
        NULL  -> no existe una comparación vigente.
        FALSE -> comparación ejecutada sin diferencias relevantes.
        TRUE  -> comparación ejecutada con diferencias relevantes.
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                TRIM(turno) AS turno,

                exp_cargado,
                resultados_cargados,
                calculo_ejecutado,
                dbf_cargado,
                comparacion_ejecutada,
                hay_diferencias,
                evento_cerrado,

                fecha_exp,
                fecha_dbf,
                fecha_calculo,
                fecha_comparacion,
                fecha_cierre

            FROM auditoria_cargas

            WHERE fecha_sorteo = %s

            ORDER BY
                CASE TRIM(turno)
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M'  THEN 3
                    WHEN 'V'  THEN 4
                    WHEN 'N'  THEN 5
                    ELSE 99
                END
            """,
            (fecha,),
        )

        return cur.fetchall()


# =========================================================
# RESULTADOS CALCULADOS POR AUDITORÍA
# =========================================================

def obtener_resultados_auditoria(
    conn: connection,
    fecha: int,
) -> list[dict]:
    """
    Obtiene los resultados de Auditoría almacenados
    en resumen_auditoria.

    Se consulta por turno + extracto.

    importe_premiados:
        importe calculado por Auditoría para ese extracto.

    apuestas_premiadas:
        cantidad correspondiente al extracto que utilizaremos
        para la columna Cupones Prem de la pantalla.
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                TRIM(turno) AS turno,
                codigo_extracto,
                sorteo AS extracto,

                COALESCE(
                    importe_premiados,
                    0
                ) AS importe_aciertos,

                COALESCE(
                    apuestas_premiadas,
                    0
                ) AS cupones_premiados

            FROM resumen_auditoria

            WHERE fecha_sorteo = %s

            ORDER BY
                CASE TRIM(turno)
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M'  THEN 3
                    WHEN 'V'  THEN 4
                    WHEN 'N'  THEN 5
                    ELSE 99
                END,
                codigo_extracto
            """,
            (fecha,),
        )

        return cur.fetchall()


# =========================================================
# CUPONES PREMIADOS DEL SISTEMA / DBF POR EXTRACTO
# =========================================================

def obtener_cupones_premiados_dbf(
    conn: connection,
    fecha: int,
) -> list[dict]:
    """
    Obtiene los cupones premiados informados por Aciertos.dbf
    para cada turno + extracto.

    No se utiliza COUNT(*) porque un mismo cupón puede tener
    más de un registro.

    La identidad del cupón es:

        agencia
        subagencia
        nromaquina
        numero
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                TRIM(turno) AS turno,
                codigo_extracto,

                COUNT(
                    DISTINCT (
                        agencia,
                        subagencia,
                        nromaquina,
                        numero
                    )
                ) AS cupones_premiados_sistema

            FROM aciertos_dbf

            WHERE fecha_sorteo = %s

            GROUP BY
                TRIM(turno),
                codigo_extracto

            ORDER BY
                CASE TRIM(turno)
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M'  THEN 3
                    WHEN 'V'  THEN 4
                    WHEN 'N'  THEN 5
                    ELSE 99
                END,
                codigo_extracto
            """,
            (fecha,),
        )

        return cur.fetchall()


# =========================================================
# CUPONES GANADORES ÚNICOS DE AUDITORÍA POR TURNO
# =========================================================

def obtener_cupones_unicos_auditoria_por_turno(
    conn: connection,
    fecha: int,
) -> list[dict]:
    """
    Obtiene la cantidad de cupones ganadores únicos
    calculados por Auditoría para cada turno.

    Si un mismo cupón gana en varios extractos del mismo
    turno, se cuenta una sola vez.

    Identidad del cupón:

        n_agent
        n_subag
        n_maqui
        n_cupon
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                TRIM(q.c_tsorteo) AS turno,

                COUNT(
                    DISTINCT (
                        q.n_agent,
                        q.n_subag,
                        q.n_maqui,
                        q.n_cupon
                    )
                ) AS cupones

            FROM premios p

            INNER JOIN quiniela_exp q
                ON q.id = p.quiniela_exp_id

            WHERE p.fecha_sorteo = %s
              AND p.premio_total > 0

            GROUP BY
                TRIM(q.c_tsorteo)

            ORDER BY
                CASE TRIM(q.c_tsorteo)
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M'  THEN 3
                    WHEN 'V'  THEN 4
                    WHEN 'N'  THEN 5
                    ELSE 99
                END
            """,
            (fecha,),
        )

        return cur.fetchall()


# =========================================================
# CUPONES GANADORES ÚNICOS DEL DBF POR TURNO
# =========================================================

def obtener_cupones_unicos_dbf_por_turno(
    conn: connection,
    fecha: int,
) -> list[dict]:
    """
    Obtiene la cantidad de cupones ganadores únicos
    informados por Aciertos.dbf para cada turno.

    Si un cupón aparece en varios extractos del mismo turno,
    se cuenta una sola vez.
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                TRIM(turno) AS turno,

                COUNT(
                    DISTINCT (
                        agencia,
                        subagencia,
                        nromaquina,
                        numero
                    )
                ) AS cupones

            FROM aciertos_dbf

            WHERE fecha_sorteo = %s

            GROUP BY
                TRIM(turno)

            ORDER BY
                CASE TRIM(turno)
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M'  THEN 3
                    WHEN 'V'  THEN 4
                    WHEN 'N'  THEN 5
                    ELSE 99
                END
            """,
            (fecha,),
        )

        return cur.fetchall()


# =========================================================
# IMPORTE TOTAL DE ACIERTOS DEL DBF POR TURNO
# =========================================================

def obtener_importes_dbf_por_turno(
    conn: connection,
    fecha: int,
) -> list[dict]:
    """
    Obtiene el importe total de aciertos informado por
    Aciertos.dbf para cada turno.

    IMPORTANTE:

    impganado representa el importe TOTAL ganado por el cupón.

    Ese mismo importe puede aparecer repetido cuando el cupón
    tiene aciertos en distintos extractos.

    Por eso NO hacemos:

        SUM(impganado)

    directamente sobre aciertos_dbf.

    Primero agrupamos el cupón completo y tomamos:

        MAX(impganado)

    Luego sumamos los importes únicos de los cupones.
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                t.turno,

                COALESCE(
                    SUM(t.importe_cupon),
                    0
                ) AS importe_aciertos_sistema

            FROM (
                SELECT
                    TRIM(turno) AS turno,
                    agencia,
                    subagencia,
                    nromaquina,
                    numero,

                    MAX(
                        COALESCE(impganado, 0)
                    ) AS importe_cupon

                FROM aciertos_dbf

                WHERE fecha_sorteo = %s

                GROUP BY
                    TRIM(turno),
                    agencia,
                    subagencia,
                    nromaquina,
                    numero

            ) AS t

            GROUP BY
                t.turno

            ORDER BY
                CASE t.turno
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M'  THEN 3
                    WHEN 'V'  THEN 4
                    WHEN 'N'  THEN 5
                    ELSE 99
                END
            """,
            (fecha,),
        )

        return cur.fetchall()


# =========================================================
# CUPONES JUGADOS ÚNICOS POR TURNO
# =========================================================

def obtener_cupones_jugados_unicos_por_turno(
    conn: connection,
    fecha: int,
) -> list[dict]:
    """
    Obtiene la cantidad real de cupones jugados por turno.

    Un mismo cupón puede contener apuestas para varios extractos,
    por lo que no se deben sumar los cupones de cada extracto.

    La identidad del cupón es:
        n_agent
        n_subag
        n_maqui
        n_cupon
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                TRIM(c_tsorteo) AS turno,

                COUNT(
                    DISTINCT (
                        n_agent,
                        n_subag,
                        n_maqui,
                        n_cupon
                    )
                ) AS cupones_jugados

            FROM quiniela_exp

            WHERE n_fsorteo = %s
              AND COALESCE(c_ecupon, '') = 'N'
              AND COALESCE(n_nodef, 0) <> 1
              AND n_impapos > 0

            GROUP BY TRIM(c_tsorteo)

            ORDER BY
                CASE TRIM(c_tsorteo)
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M'  THEN 3
                    WHEN 'V'  THEN 4
                    WHEN 'N'  THEN 5
                    ELSE 99
                END
            """,
            (fecha,),
        )

        return cur.fetchall()


# =========================================================
# CUPONES JUGADOS ÚNICOS DE TODA LA JORNADA
# =========================================================

def obtener_cupones_jugados_unicos_jornada(
    conn: connection,
    fecha: int,
) -> int:
    """
    Obtiene los cupones jugados únicos de toda la jornada.

    Se incluye el turno en la identidad para evitar considerar
    como el mismo cupón dos cupones pertenecientes a sorteos
    distintos del mismo día.
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(
                DISTINCT (
                    TRIM(c_tsorteo),
                    n_agent,
                    n_subag,
                    n_maqui,
                    n_cupon
                )
            )

            FROM quiniela_exp

            WHERE n_fsorteo = %s
              AND COALESCE(c_ecupon, '') = 'N'
              AND COALESCE(n_nodef, 0) <> 1
              AND n_impapos > 0
            """,
            (fecha,),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0
    