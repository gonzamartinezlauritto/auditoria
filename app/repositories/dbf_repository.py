from decimal import Decimal

from psycopg2.extensions import connection


def eliminar_aciertos_por_fecha_turno(
    conn: connection,
    fecha: int,
    turno: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM aciertos_dbf
            WHERE fecha_sorteo = %s
              AND turno = %s
            """,
            (
                fecha,
                turno,
            ),
        )


def insertar_acierto(
    conn: connection,
    *,
    fecha: int,
    turno: str,
    codigo_extracto: int | None,
    agencia: int | None,
    subagencia: int | None,
    nromaquina: int | None,
    numero: int | None,
    apuestas: int | None,
    ap_acierto: int | None,
    apostado: Decimal,
    impganado: Decimal,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO aciertos_dbf (
                fecha_sorteo,
                turno,
                codigo_extracto,
                agencia,
                subagencia,
                nromaquina,
                numero,
                apuestas,
                ap_acierto,
                apostado,
                impganado
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                fecha,
                turno,
                codigo_extracto,
                agencia,
                subagencia,
                nromaquina,
                numero,
                apuestas,
                ap_acierto,
                apostado,
                impganado,
            ),
        )


def obtener_resumen_extractos(
    conn: connection,
    fecha: int,
    turno: str,
) -> list[dict[str, int | None]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                codigo_extracto,
                COUNT(*)
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

        return [
            {
                "codigo_extracto": row[0],
                "cantidad": row[1],
            }
            for row in cur.fetchall()
        ]


def contar_cupones_ganadores_unicos(
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
            ) AS cupones_unicos
            """,
            (
                fecha,
                turno,
            ),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0