from psycopg2.extensions import connection


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
            (
                fecha,
                turno,
            ),
        )

        return cur.fetchall()


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
            (
                fecha,
                turno,
            ),
        )

        return cur.fetchall()


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
            (
                fecha,
                turno,
            ),
        )

        return cur.fetchall()


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
            (
                fecha,
                turno,
            ),
        )

        return cur.fetchall()


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
            (
                fecha,
                turno,
            ),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0


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
            (
                fecha,
                turno,
            ),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0


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
            (
                cantidad,
                fecha,
                turno,
            ),
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
    Devuelve el monto total ganado por cada cupón
    considerando TODOS los extractos.

    Clave:
    (
        agencia,
        subagencia,
        maquina,
        cupon
    )

    premio_total está almacenado en unidades internas,
    por eso se divide por 100.
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
            (
                fecha,
                turno,
            ),
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
    Devuelve el monto total ganado por cada cupón según DBF.

    impganado puede repetirse en distintas filas/extractos
    del mismo cupón.

    Por eso NO usamos SUM(impganado).
    Tomamos MAX(impganado), ya que representa
    el total ganado por el cupón.
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
            (
                fecha,
                turno,
            ),
        )

        return cur.fetchall()