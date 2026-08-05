from pathlib import Path

from psycopg2.extensions import connection

from app.constants.turnos import TURNOS_VALIDOS


CREATE_TEMP_TABLE_SQL = """
    CREATE TEMP TABLE quiniela_exp_tmp (
        n_apues BIGINT,
        n_maqre BIGINT,
        n_agent INTEGER,
        n_subag INTEGER,
        n_maqui INTEGER,
        n_cupon BIGINT,
        n_linea INTEGER,
        n_femis INTEGER,
        c_hemis TIME,
        c_ecupon VARCHAR(10),
        n_fsorteo INTEGER,
        n_codlot INTEGER,
        c_tsorteo VARCHAR(10),
        n_alcdes INTEGER,
        n_alchas INTEGER,
        c_nroapos VARCHAR(20),
        n_impapos NUMERIC(18,2),
        n_nodef INTEGER,
        n_codext INTEGER
    ) ON COMMIT DROP
"""


COPY_TEMP_TABLE_SQL = """
    COPY quiniela_exp_tmp (
        n_apues,
        n_maqre,
        n_agent,
        n_subag,
        n_maqui,
        n_cupon,
        n_linea,
        n_femis,
        c_hemis,
        c_ecupon,
        n_fsorteo,
        n_codlot,
        c_tsorteo,
        n_alcdes,
        n_alchas,
        c_nroapos,
        n_impapos,
        n_nodef,
        n_codext
    )
    FROM STDIN
    WITH (
        FORMAT csv,
        DELIMITER ',',
        QUOTE '"'
    )
"""


INSERT_APUESTAS_SQL = """
    INSERT INTO quiniela_exp (
        n_apues,
        n_maqre,
        n_agent,
        n_subag,
        n_maqui,
        n_cupon,
        n_linea,
        n_femis,
        c_hemis,
        c_ecupon,
        n_fsorteo,
        n_codlot,
        c_tsorteo,
        n_alcdes,
        n_alchas,
        c_nroapos,
        n_impapos,
        n_nodef,
        n_codext,
        archivo_origen,
        fecha_carga
    )
    SELECT
        n_apues,
        n_maqre,
        n_agent,
        n_subag,
        n_maqui,
        n_cupon,
        n_linea,
        n_femis,
        c_hemis,
        c_ecupon,
        n_fsorteo,
        n_codlot,
        UPPER(TRIM(c_tsorteo)),
        n_alcdes,
        n_alchas,
        c_nroapos,
        n_impapos,
        n_nodef,
        n_codext,
        %s,
        NOW()
    FROM quiniela_exp_tmp
    WHERE UPPER(TRIM(c_tsorteo)) = ANY(%s)
    ON CONFLICT DO NOTHING
"""


def crear_tabla_temporal(
    conn: connection,
) -> None:
    with conn.cursor() as cur:
        cur.execute(CREATE_TEMP_TABLE_SQL)


def copiar_archivo_a_temporal(
    conn: connection,
    file_path: Path,
) -> None:
    with conn.cursor() as cur:
        with file_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as archivo:
            cur.copy_expert(
                COPY_TEMP_TABLE_SQL,
                archivo,
            )


def contar_total_temporal(
    conn: connection,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM quiniela_exp_tmp
            """
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0


def contar_turnos_validos_temporal(
    conn: connection,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM quiniela_exp_tmp
            WHERE UPPER(TRIM(c_tsorteo)) = ANY(%s)
            """,
            (
                list(TURNOS_VALIDOS),
            ),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0


def obtener_turnos_ignorados(
    conn: connection,
) -> list[dict[str, int | str]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COALESCE(
                    NULLIF(
                        UPPER(TRIM(c_tsorteo)),
                        ''
                    ),
                    '<VACIO>'
                ) AS turno,
                COUNT(*) AS cantidad
            FROM quiniela_exp_tmp
            WHERE c_tsorteo IS NULL
               OR TRIM(c_tsorteo) = ''
               OR NOT (
                    UPPER(TRIM(c_tsorteo)) = ANY(%s)
               )
            GROUP BY
                COALESCE(
                    NULLIF(
                        UPPER(TRIM(c_tsorteo)),
                        ''
                    ),
                    '<VACIO>'
                )
            ORDER BY turno
            """,
            (
                list(TURNOS_VALIDOS),
            ),
        )

        return [
            {
                "turno": row[0],
                "cantidad": row[1],
            }
            for row in cur.fetchall()
        ]


def insertar_apuestas_validas(
    conn: connection,
    archivo_origen: str,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            INSERT_APUESTAS_SQL,
            (
                archivo_origen,
                list(TURNOS_VALIDOS),
            ),
        )

        return cur.rowcount


def registrar_carga(
    conn: connection,
    archivo_origen: str,
    fecha: int,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO cargas_exp (
                archivo_origen,
                fecha_archivo
            )
            VALUES (%s, %s)
            ON CONFLICT (archivo_origen)
            DO UPDATE SET
                fecha_archivo = EXCLUDED.fecha_archivo,
                fecha_carga = NOW()
            """,
            (
                archivo_origen,
                fecha,
            ),
        )


def contar_apuestas_por_fecha_turno(
    conn: connection,
    fecha: int,
    turno: str,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND UPPER(TRIM(c_tsorteo)) = %s
            """,
            (
                fecha,
                turno.upper().strip(),
            ),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0