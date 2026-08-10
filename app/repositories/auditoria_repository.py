from psycopg2.extensions import connection


def marcar_exp_cargado(
    conn: connection,
    fecha: int,
    turno: str,
    archivo_exp: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO auditoria_cargas (
                fecha_sorteo,
                turno,
                exp_cargado,
                archivo_exp,
                fecha_exp,
                updated_at
            )
            VALUES (%s, %s, TRUE, %s, NOW(), NOW())
            ON CONFLICT (fecha_sorteo, turno)
            DO UPDATE SET
                exp_cargado = TRUE,
                archivo_exp = EXCLUDED.archivo_exp,
                fecha_exp = NOW(),
                updated_at = NOW()
            """,
            (
                fecha,
                turno,
                archivo_exp,
            ),
        )


def marcar_dbf_cargado(
    conn: connection,
    fecha: int,
    turno: str,
    archivo_dbf: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO auditoria_cargas (
                fecha_sorteo,
                turno,
                dbf_cargado,
                archivo_dbf,
                fecha_dbf,
                updated_at
            )
            VALUES (%s, %s, TRUE, %s, NOW(), NOW())
            ON CONFLICT (fecha_sorteo, turno)
            DO UPDATE SET
                dbf_cargado = TRUE,
                archivo_dbf = EXCLUDED.archivo_dbf,
                fecha_dbf = NOW(),
                updated_at = NOW()
            """,
            (
                fecha,
                turno,
                archivo_dbf,
            ),
        )


def marcar_resultados_cargados(
    conn: connection,
    fecha: int,
    turno: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO auditoria_cargas (
                fecha_sorteo,
                turno,
                resultados_cargados,
                updated_at
            )
            VALUES (%s, %s, TRUE, NOW())
            ON CONFLICT (fecha_sorteo, turno)
            DO UPDATE SET
                resultados_cargados = TRUE,
                updated_at = NOW()
            """,
            (
                fecha,
                turno,
            ),
        )


def marcar_calculo_ejecutado(
    conn: connection,
    fecha: int,
    turno: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO auditoria_cargas (
                fecha_sorteo,
                turno,
                calculo_ejecutado,
                fecha_calculo,
                updated_at
            )
            VALUES (%s, %s, TRUE, NOW(), NOW())
            ON CONFLICT (fecha_sorteo, turno)
            DO UPDATE SET
                calculo_ejecutado = TRUE,
                fecha_calculo = NOW(),
                updated_at = NOW()
            """,
            (
                fecha,
                turno,
            ),
        )


def obtener_estado_por_fecha(
    conn: connection,
    fecha: int,
) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                fecha_sorteo,
                turno,
                exp_cargado,
                resultados_cargados,
                dbf_cargado,
                calculo_ejecutado,
                archivo_exp,
                archivo_dbf,
                fecha_exp,
                fecha_dbf,
                fecha_calculo,
                updated_at
            FROM auditoria_cargas
            WHERE fecha_sorteo = %s
            ORDER BY
                CASE turno
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M' THEN 3
                    WHEN 'V' THEN 4
                    WHEN 'N' THEN 5
                    ELSE 99
                END
            """,
            (
                fecha,
            ),
        )

        return cur.fetchall()