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