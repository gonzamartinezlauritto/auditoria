from psycopg2.extensions import connection


def eliminar_resultados_extracto(
    conn: connection,
    fecha: int,
    turno: str,
    codigo_extracto: int,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM resultados
            WHERE fecha_sorteo = %s
              AND turno = %s
              AND codigo_extracto = %s
            """,
            (
                fecha,
                turno,
                codigo_extracto,
            ),
        )


def insertar_resultado(
    conn: connection,
    *,
    fecha: int,
    turno: str,
    codigo_extracto: int,
    orden: int,
    numero: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO resultados (
                fecha_sorteo,
                turno,
                codigo_extracto,
                orden_resultado,
                numero_resultado
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                fecha,
                turno,
                codigo_extracto,
                orden,
                numero,
            ),
        )


def obtener_resultados_por_fecha(
    conn: connection,
    fecha: int,
) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                r.turno,
                r.codigo_extracto,
                e.nombre_extracto,
                r.orden_resultado,
                r.numero_resultado
            FROM resultados r
            JOIN extractos e
                ON e.codigo_extracto = r.codigo_extracto
            WHERE r.fecha_sorteo = %s
            ORDER BY
                r.turno,
                r.codigo_extracto,
                r.orden_resultado
            """,
            (
                fecha,
            ),
        )

        return cur.fetchall()