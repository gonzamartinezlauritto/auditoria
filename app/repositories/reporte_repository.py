from psycopg2.extensions import connection


def obtener_control_aciertos(
    conn: connection,
    fecha: int,
    turno: str,
) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                r.codigo_extracto,
                r.sorteo,
                r.cupones_jugados,
                r.recaudacion,
                r.importe_premiados,
                r.comision,
                r.utilidad,
                r.porcentaje_utilidad,
                r.apuestas_premiadas,

                COALESCE(
                    dbf.generados_frontend,
                    0
                ) AS generados_frontend,

                r.cupones_ganadores_unicos,

                COALESCE(
                    dbf.cupones_ganadores_dbf,
                    0
                ) AS cupones_ganadores_dbf

            FROM resumen_auditoria r

            LEFT JOIN (
                SELECT
                    fecha_sorteo,
                    turno,
                    codigo_extracto,

                    COUNT(*) AS generados_frontend,

                    COUNT(
                        DISTINCT (
                            agencia,
                            subagencia,
                            nromaquina,
                            numero
                        )
                    ) AS cupones_ganadores_dbf

                FROM aciertos_dbf

                WHERE fecha_sorteo = %s
                  AND turno = %s

                GROUP BY
                    fecha_sorteo,
                    turno,
                    codigo_extracto
            ) dbf
                ON dbf.fecha_sorteo = r.fecha_sorteo
               AND dbf.turno = r.turno
               AND dbf.codigo_extracto = r.codigo_extracto

            WHERE r.fecha_sorteo = %s
              AND r.turno = %s

            ORDER BY
                CASE r.codigo_extracto
                    WHEN 52 THEN 1
                    WHEN 56 THEN 2
                    WHEN 51 THEN 3
                    WHEN 54 THEN 4
                    WHEN 50 THEN 5
                    WHEN 55 THEN 6
                    WHEN 53 THEN 7
                    ELSE 99
                END
            """,
            (
                fecha,
                turno,
                fecha,
                turno,
            ),
        )

        return cur.fetchall()


def obtener_cupones_ganadores_unicos_frontend(
    conn: connection,
    fecha: int,
    turno: str,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    agencia,
                    subagencia,
                    nromaquina,
                    numero
                FROM aciertos_dbf
                WHERE fecha_sorteo = %s
                  AND turno = %s
                GROUP BY
                    agencia,
                    subagencia,
                    nromaquina,
                    numero
            ) t
            """,
            (
                fecha,
                turno,
            ),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0


def obtener_importe_total_frontend(
    conn: connection,
    fecha: int,
    turno: str,
):
    """
    Obtiene el importe total ganado según el DBF.

    impganado representa el premio TOTAL del cupón
    y puede aparecer repetido en varios extractos.

    Por eso:
    1. agrupamos globalmente por cupón
    2. tomamos MAX(impganado)
    3. recién después sumamos esos importes
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(
                SUM(t.importe_cupon),
                0
            )
            FROM (
                SELECT
                    agencia,
                    subagencia,
                    nromaquina,
                    numero,
                    MAX(impganado) AS importe_cupon

                FROM aciertos_dbf

                WHERE fecha_sorteo = %s
                  AND turno = %s

                GROUP BY
                    agencia,
                    subagencia,
                    nromaquina,
                    numero
            ) t
            """,
            (
                fecha,
                turno,
            ),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0