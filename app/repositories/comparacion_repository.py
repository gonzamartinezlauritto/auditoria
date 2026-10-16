from psycopg2.extensions import connection


# ============================================================
# GANADORES - SISTEMA
# ============================================================

def obtener_ganadores_sistema(
    conn: connection,
    fecha: int,
    turno: str,
) -> list[tuple]:

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT
                p.codigo_extracto,
                q.n_agent,
                q.n_subag,
                q.n_maqui,
                q.n_cupon
            FROM premios p
            JOIN quiniela_exp q
                ON q.id = p.quiniela_exp_id
            WHERE p.fecha_sorteo = %s
              AND TRIM(q.c_tsorteo) = %s
              AND p.premio_total > 0
            ORDER BY
                p.codigo_extracto,
                q.n_agent,
                q.n_subag,
                q.n_maqui,
                q.n_cupon
            """,
            (fecha, turno),
        )

        return cur.fetchall()


# ============================================================
# GANADORES - DBF
# ============================================================

def obtener_ganadores_dbf(
    conn: connection,
    fecha: int,
    turno: str,
) -> list[tuple]:

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT
                codigo_extracto,
                agencia,
                subagencia,
                nromaquina,
                numero
            FROM aciertos_dbf
            WHERE fecha_sorteo = %s
              AND turno = %s
            ORDER BY
                codigo_extracto,
                agencia,
                subagencia,
                nromaquina,
                numero
            """,
            (fecha, turno),
        )

        return cur.fetchall()


# ============================================================
# ACIERTOS POR EXTRACTO - SISTEMA
# ============================================================

def obtener_aciertos_sistema_por_extracto(
    conn: connection,
    fecha: int,
    turno: str,
) -> list[tuple]:

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                p.codigo_extracto,
                COUNT(DISTINCT (
                    q.n_agent,
                    q.n_subag,
                    q.n_maqui,
                    q.n_cupon
                )) AS cantidad
            FROM premios p
            JOIN quiniela_exp q
                ON q.id = p.quiniela_exp_id
            WHERE p.fecha_sorteo = %s
              AND TRIM(q.c_tsorteo) = %s
              AND p.premio_total > 0
            GROUP BY p.codigo_extracto
            ORDER BY p.codigo_extracto
            """,
            (fecha, turno),
        )

        return cur.fetchall()


# ============================================================
# ACIERTOS POR EXTRACTO - DBF
# ============================================================

def obtener_aciertos_dbf_por_extracto(
    conn: connection,
    fecha: int,
    turno: str,
) -> list[tuple]:

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                codigo_extracto,
                COUNT(*) AS cantidad
            FROM aciertos_dbf
            WHERE fecha_sorteo = %s
              AND turno = %s
            GROUP BY codigo_extracto
            ORDER BY codigo_extracto
            """,
            (fecha, turno),
        )

        return cur.fetchall()


# ============================================================
# CUPONES GANADORES ÚNICOS - SISTEMA
# ============================================================

def contar_cupones_ganadores_unicos_sistema(
    conn: connection,
    fecha: int,
    turno: str,
) -> int:

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT
                    q.n_agent,
                    q.n_subag,
                    q.n_maqui,
                    q.n_cupon
                FROM premios p
                JOIN quiniela_exp q
                    ON q.id = p.quiniela_exp_id
                WHERE p.fecha_sorteo = %s
                  AND TRIM(q.c_tsorteo) = %s
                  AND p.premio_total > 0
            ) t
            """,
            (fecha, turno),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0


# ============================================================
# CUPONES GANADORES ÚNICOS - DBF
# ============================================================

def contar_cupones_ganadores_unicos_dbf(
    conn: connection,
    fecha: int,
    turno: str,
) -> int:

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT
                    agencia,
                    subagencia,
                    nromaquina,
                    numero
                FROM aciertos_dbf
                WHERE fecha_sorteo = %s
                  AND turno = %s
            ) t
            """,
            (fecha, turno),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0


# ============================================================
# ACTUALIZAR CUPONES DBF EN RESUMEN
# ============================================================

def actualizar_cupones_dbf_resumen(
    conn: connection,
    fecha: int,
    turno: str,
    cantidad: int,
) -> None:

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE resumen_auditoria
            SET cupones_ganadores_dbf = %s
            WHERE fecha_sorteo = %s
              AND turno = %s
            """,
            (cantidad, fecha, turno),
        )


# ============================================================
# MONTOS POR CUPÓN - SISTEMA
# ============================================================

def obtener_montos_sistema_por_cupon(
    conn: connection,
    fecha: int,
    turno: str,
) -> list[tuple]:
    """
    Obtiene el importe total ganado por cada cupón,
    considerando todos los extractos.

    premio_total se divide por 100 para obtener pesos.
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                q.n_agent,
                q.n_subag,
                q.n_maqui,
                q.n_cupon,
                COALESCE(
                    SUM(p.premio_total),
                    0
                ) / 100.0 AS monto
            FROM premios p
            JOIN quiniela_exp q
                ON q.id = p.quiniela_exp_id
            WHERE p.fecha_sorteo = %s
              AND TRIM(q.c_tsorteo) = %s
              AND p.premio_total > 0
            GROUP BY
                q.n_agent,
                q.n_subag,
                q.n_maqui,
                q.n_cupon
            ORDER BY
                q.n_agent,
                q.n_subag,
                q.n_maqui,
                q.n_cupon
            """,
            (fecha, turno),
        )

        return cur.fetchall()


# ============================================================
# MONTOS POR CUPÓN - DBF
# ============================================================

def obtener_montos_dbf_por_cupon(
    conn: connection,
    fecha: int,
    turno: str,
) -> list[tuple]:
    """
    impganado puede repetirse entre extractos del mismo
    cupón porque representa el total global ganado.

    Por eso utilizamos MAX y no SUM.
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                agencia,
                subagencia,
                nromaquina,
                numero,
                COALESCE(
                    MAX(impganado),
                    0
                ) AS monto
            FROM aciertos_dbf
            WHERE fecha_sorteo = %s
              AND TRIM(turno) = %s
            GROUP BY
                agencia,
                subagencia,
                nromaquina,
                numero
            ORDER BY
                agencia,
                subagencia,
                nromaquina,
                numero
            """,
            (fecha, turno),
        )

        return cur.fetchall()


# ============================================================
# EXTRACTOS PREMIADOS DE CUPONES CON DIFERENCIAS MONETARIAS
# ============================================================

def obtener_extractos_por_cupones(
    conn: connection,
    fecha: int,
    turno: str,
    cupones: list[tuple],
) -> list[int]:
    """
    Obtiene los extractos premiados asociados a los
    cupones con diferencias monetarias.

    Considera:
      - premios del sistema
      - aciertos del DBF

    No incluye extractos donde el cupón solamente
    tenga apuestas perdedoras.

    Si el cupón tiene premios en varios extractos,
    devuelve todos los extractos involucrados.
    """

    if not cupones:
        return []

    agencias = [int(c[0]) for c in cupones]
    subagencias = [int(c[1]) for c in cupones]
    maquinas = [int(c[2]) for c in cupones]
    numeros = [int(c[3]) for c in cupones]

    with conn.cursor() as cur:
        cur.execute(
            """
            WITH cupones_buscados (
                agencia,
                subagencia,
                maquina,
                cupon
            ) AS (
                SELECT *
                FROM UNNEST(
                    %s::integer[],
                    %s::integer[],
                    %s::integer[],
                    %s::integer[]
                )
            )
            SELECT DISTINCT codigo_extracto
            FROM (
                SELECT
                    p.codigo_extracto
                FROM premios p
                JOIN quiniela_exp q
                    ON q.id = p.quiniela_exp_id
                JOIN cupones_buscados c
                    ON q.n_agent = c.agencia
                   AND q.n_subag = c.subagencia
                   AND q.n_maqui = c.maquina
                   AND q.n_cupon = c.cupon
                WHERE p.fecha_sorteo = %s
                  AND TRIM(q.c_tsorteo) = %s
                  AND p.premio_total > 0

                UNION

                SELECT
                    d.codigo_extracto
                FROM aciertos_dbf d
                JOIN cupones_buscados c
                    ON d.agencia = c.agencia
                   AND d.subagencia = c.subagencia
                   AND d.nromaquina = c.maquina
                   AND d.numero = c.cupon
                WHERE d.fecha_sorteo = %s
                  AND TRIM(d.turno) = %s
            ) extractos
            WHERE codigo_extracto IS NOT NULL
            ORDER BY codigo_extracto
            """,
            (
                agencias,
                subagencias,
                maquinas,
                numeros,
                fecha,
                turno,
                fecha,
                turno,
            ),
        )

        return [int(row[0]) for row in cur.fetchall()]


# ============================================================
# NUEVO: IMPORTES APOSTADOS POR EXTRACTO
# ============================================================

def obtener_importes_apostados_por_extracto(
    conn: connection,
    fecha: int,
    turno: str,
) -> list[tuple]:
    """
    Obtiene la recaudación registrada en quiniela_exp
    por fecha, turno y extracto.

    Incluye todas las apuestas:
      - ganadoras
      - perdedoras

    n_impapos se divide por 100 para obtener pesos.

    No modifica ni consulta los premios calculados.
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                n_codext AS codigo_extracto,
                COALESCE(
                    SUM(n_impapos),
                    0
                ) / 100.0 AS importe_apostado
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND TRIM(c_tsorteo) = %s
            GROUP BY n_codext
            ORDER BY n_codext
            """,
            (fecha, turno),
        )

        return cur.fetchall()