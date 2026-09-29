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
    Obtiene toda la información de apuestas necesaria para
    representar la jornada completa.

    Devuelve por turno + extracto:
    - turno
    - código de extracto
    - nombre del extracto
    - recaudación
    - cupones jugados del extracto
    - cupones jugados únicos del turno
    - cupones jugados únicos de toda la jornada

    La consulta procesa quiniela_exp una sola vez.

    Primero reduce las apuestas a una fila por:
        turno + extracto + agencia + subagencia + máquina + cupón

    A partir de esa base reducida calcula los distintos niveles
    de agregación necesarios para la pantalla.

    Los importes de quiniela_exp están almacenados x100,
    por lo que la recaudación se divide por 100.
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            WITH base AS MATERIALIZED (
                SELECT
                    TRIM(c_tsorteo) AS turno,
                    n_codext AS codigo_extracto,
                    n_agent,
                    n_subag,
                    n_maqui,
                    n_cupon,
                    SUM(n_impapos) AS importe

                FROM quiniela_exp

                WHERE n_fsorteo = %s
                  AND COALESCE(c_ecupon, '') = 'N'
                  AND COALESCE(n_nodef, 0) <> 1
                  AND n_impapos > 0

                GROUP BY
                    TRIM(c_tsorteo),
                    n_codext,
                    n_agent,
                    n_subag,
                    n_maqui,
                    n_cupon
            ),

            por_extracto AS (
                SELECT
                    turno,
                    codigo_extracto,

                    SUM(importe) / 100.0 AS recaudacion,

                    COUNT(*) AS cupones_jugados

                FROM base

                GROUP BY
                    turno,
                    codigo_extracto
            ),

            cupones_turno AS (
                SELECT
                    turno,
                    COUNT(*) AS cupones_jugados_turno

                FROM (
                    SELECT DISTINCT
                        turno,
                        n_agent,
                        n_subag,
                        n_maqui,
                        n_cupon

                    FROM base
                ) AS t

                GROUP BY turno
            ),

            cupones_jornada AS (
                SELECT
                    COUNT(*) AS cupones_jugados_jornada

                FROM (
                    SELECT DISTINCT
                        turno,
                        n_agent,
                        n_subag,
                        n_maqui,
                        n_cupon

                    FROM base
                ) AS j
            )

            SELECT
                pe.turno,
                pe.codigo_extracto,
                e.nombre_extracto AS extracto,
                pe.recaudacion,
                pe.cupones_jugados,
                ct.cupones_jugados_turno,
                cj.cupones_jugados_jornada

            FROM por_extracto pe

            LEFT JOIN extractos e
                ON e.codigo_extracto = pe.codigo_extracto

            INNER JOIN cupones_turno ct
                ON ct.turno = pe.turno

            CROSS JOIN cupones_jornada cj

            ORDER BY
                CASE pe.turno
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M'  THEN 3
                    WHEN 'V'  THEN 4
                    WHEN 'N'  THEN 5
                    ELSE 99
                END,
                pe.codigo_extracto
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

