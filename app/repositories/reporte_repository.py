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
                codigo_extracto,
                sorteo,
                cupones_jugados,
                recaudacion,
                importe_premiados,
                comision,
                utilidad,
                porcentaje_utilidad,
                apuestas_premiadas,
                archivo_aciertos_dbf,
                cupones_ganadores_unicos,
                cupones_ganadores_dbf
            FROM resumen_auditoria
            WHERE fecha_sorteo = %s
              AND turno = %s
            ORDER BY
                CASE codigo_extracto
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
            ),
        )

        return cur.fetchall()