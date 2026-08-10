from decimal import Decimal

from psycopg2.extensions import connection


def obtener_extractos_del_turno(
    conn: connection,
    fecha: int,
    turno: str,
) -> list[int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT n_codext
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND TRIM(c_tsorteo) = %s
              AND COALESCE(c_ecupon, '') = 'N'
              AND COALESCE(n_nodef, 0) <> 1
            ORDER BY n_codext
            """,
            (
                fecha,
                turno,
            ),
        )

        return [
            row[0]
            for row in cur.fetchall()
        ]


def obtener_estado_cargas(
    conn: connection,
    fecha: int,
    turno: str,
):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                exp_cargado,
                resultados_cargados,
                dbf_cargado
            FROM auditoria_cargas
            WHERE fecha_sorteo = %s
              AND turno = %s
            """,
            (
                fecha,
                turno,
            ),
        )

        return cur.fetchone()


def obtener_extracto(
    conn: connection,
    codigo_extracto: int,
):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                codigo_extracto,
                provincia,
                nombre_extracto,
                premio_4_cifras,
                premio_3_cifras,
                premio_2_cifras,
                premio_1_cifra,
                aprox_4_cifras,
                aprox_3_cifras,
                tope_redoblona
            FROM extractos
            WHERE codigo_extracto = %s
            """,
            (
                codigo_extracto,
            ),
        )

        return cur.fetchone()


def eliminar_premios_extracto(
    conn: connection,
    fecha: int,
    turno: str,
    codigo_extracto: int,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM premios
            WHERE fecha_sorteo = %s
              AND codigo_extracto = %s
              AND quiniela_exp_id IN (
                  SELECT id
                  FROM quiniela_exp
                  WHERE n_fsorteo = %s
                    AND c_tsorteo = %s
                    AND n_codext = %s
              )
            """,
            (
                fecha,
                codigo_extracto,
                fecha,
                turno,
                codigo_extracto,
            ),
        )


def obtener_resultados_extracto(
    conn: connection,
    fecha: int,
    turno: str,
    codigo_extracto: int,
) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                orden_resultado,
                numero_resultado
            FROM resultados
            WHERE fecha_sorteo = %s
              AND turno = %s
              AND codigo_extracto = %s
            ORDER BY orden_resultado
            """,
            (
                fecha,
                turno,
                codigo_extracto,
            ),
        )

        return cur.fetchall()


def obtener_apuestas_extracto(
    conn: connection,
    fecha: int,
    turno: str,
    codigo_extracto: int,
) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
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
                COALESCE(es_redoblona_base, false),
                COALESCE(es_redoblona_detalle, false),
                linea_base_id,
                redoblona_grupo
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND c_tsorteo = %s
              AND n_codext = %s
              AND COALESCE(c_ecupon, '') = 'N'
              AND COALESCE(n_nodef, 0) <> 1
            ORDER BY
                n_agent,
                n_subag,
                n_maqui,
                n_cupon,
                n_linea,
                id
            """,
            (
                fecha,
                turno,
                codigo_extracto,
            ),
        )

        return cur.fetchall()


def insertar_premio(
    conn: connection,
    data: tuple,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO premios (
                quiniela_exp_id,
                fecha_sorteo,
                codigo_extracto,
                numero_apostado,
                numero_resultado,
                orden_resultado,
                cifras_acertadas,
                importe_apostado,
                multiplicador,
                premio_total,
                tipo_jugada,
                quiniela_exp_id_redoblona,
                premio_base_redoblona
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            )
            """,
            data,
        )


def obtener_total_premios_normales(
    conn: connection,
    fecha: int,
    turno: str,
    codigo_extracto: int,
) -> Decimal:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(
                SUM(p.premio_total),
                0
            )
            FROM premios p
            JOIN quiniela_exp q
                ON q.id = p.quiniela_exp_id
            WHERE p.fecha_sorteo = %s
              AND p.codigo_extracto = %s
              AND q.c_tsorteo = %s
              AND p.tipo_jugada = 'normal'
            """,
            (
                fecha,
                codigo_extracto,
                turno,
            ),
        )

        resultado = cur.fetchone()

        return Decimal(
            str(
                resultado[0]
                if resultado
                else 0
            )
        )


def obtener_total_aproximaciones(
    conn: connection,
    fecha: int,
    turno: str,
    codigo_extracto: int,
) -> Decimal:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(
                SUM(p.premio_total),
                0
            )
            FROM premios p
            JOIN quiniela_exp q
                ON q.id = p.quiniela_exp_id
            WHERE p.fecha_sorteo = %s
              AND p.codigo_extracto = %s
              AND q.c_tsorteo = %s
              AND p.tipo_jugada IN (
                  'aprox_3',
                  'aprox_4'
              )
            """,
            (
                fecha,
                codigo_extracto,
                turno,
            ),
        )

        resultado = cur.fetchone()

        return Decimal(
            str(
                resultado[0]
                if resultado
                else 0
            )
        )


def obtener_total_redoblonas(
    conn: connection,
    fecha: int,
    turno: str,
    codigo_extracto: int,
) -> Decimal:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(
                SUM(p.premio_total),
                0
            )
            FROM premios p
            JOIN quiniela_exp q
                ON q.id = p.quiniela_exp_id
            WHERE p.fecha_sorteo = %s
              AND p.codigo_extracto = %s
              AND q.c_tsorteo = %s
              AND p.tipo_jugada = 'redoblona'
            """,
            (
                fecha,
                codigo_extracto,
                turno,
            ),
        )

        resultado = cur.fetchone()

        return Decimal(
            str(
                resultado[0]
                if resultado
                else 0
            )
        )


def contar_apuestas_premiadas(
    conn: connection,
    fecha: int,
    turno: str,
    codigo_extracto: int,
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
                  AND p.codigo_extracto = %s
                  AND TRIM(q.c_tsorteo) = %s
                  AND p.premio_total > 0
            ) t
            """,
            (
                fecha,
                codigo_extracto,
                turno,
            ),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0


def obtener_total_recaudado(
    conn: connection,
    fecha: int,
    turno: str,
    codigo_extracto: int,
) -> Decimal:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(
                SUM(n_impapos),
                0
            )
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND c_tsorteo = %s
              AND n_codext = %s
              AND COALESCE(c_ecupon, '') = 'N'
              AND COALESCE(n_nodef, 0) <> 1
              AND n_impapos > 0
            """,
            (
                fecha,
                turno,
                codigo_extracto,
            ),
        )

        resultado = cur.fetchone()

        return Decimal(
            str(
                resultado[0]
                if resultado
                else 0
            )
        )


def contar_cupones_jugados(
    conn: connection,
    fecha: int,
    turno: str,
    codigo_extracto: int,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    n_agent,
                    n_subag,
                    n_maqui,
                    n_cupon
                FROM quiniela_exp
                WHERE n_fsorteo = %s
                  AND c_tsorteo = %s
                  AND n_codext = %s
                  AND COALESCE(c_ecupon, '') = 'N'
                  AND COALESCE(n_nodef, 0) <> 1
                GROUP BY
                    n_agent,
                    n_subag,
                    n_maqui,
                    n_cupon
            ) t
            """,
            (
                fecha,
                turno,
                codigo_extracto,
            ),
        )

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0


def contar_aciertos_dbf_extracto(
    conn: connection,
    fecha: int,
    turno: str,
    codigo_extracto: int,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM aciertos_dbf
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

        resultado = cur.fetchone()

        return resultado[0] if resultado else 0


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
                    q.n_agent,
                    q.n_subag,
                    q.n_maqui,
                    q.n_cupon
                FROM premios p
                JOIN quiniela_exp q
                    ON q.id = p.quiniela_exp_id
                WHERE p.fecha_sorteo = %s
                  AND TRIM(q.c_tsorteo) = %s
                  AND p.premio_total <> 0
                GROUP BY
                    q.n_agent,
                    q.n_subag,
                    q.n_maqui,
                    q.n_cupon
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


def guardar_resumen_extracto(
    conn: connection,
    fecha: int,
    turno: str,
    reporte: dict,
    cupones_ganadores_unicos: int
) -> None:
    recaudacion = Decimal(
        str(
            reporte["recaudacion"]
        )
    )

    importe_premiados = Decimal(
        str(
            reporte["importe_premiados"]
        )
    )

    comision = (
        recaudacion
        * Decimal("0.20")
    ).quantize(
        Decimal("0.01")
    )

    utilidad = (
        recaudacion
        - importe_premiados
        - comision
    ).quantize(
        Decimal("0.01")
    )

    porcentaje_utilidad = Decimal("0.00")

    if recaudacion > 0:
        porcentaje_utilidad = (
            (
                utilidad
                / recaudacion
            )
            * Decimal("100")
        ).quantize(
            Decimal("0.01")
        )

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO resumen_auditoria (
                fecha_sorteo,
                turno,
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
                cupones_ganadores_dbf,
                fecha_calculo
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, NULL, NOW()
            )
            ON CONFLICT (
                fecha_sorteo,
                turno,
                codigo_extracto
            )
            DO UPDATE SET
                sorteo = EXCLUDED.sorteo,
                cupones_jugados = EXCLUDED.cupones_jugados,
                recaudacion = EXCLUDED.recaudacion,
                importe_premiados = EXCLUDED.importe_premiados,
                comision = EXCLUDED.comision,
                utilidad = EXCLUDED.utilidad,
                porcentaje_utilidad = EXCLUDED.porcentaje_utilidad,
                apuestas_premiadas = EXCLUDED.apuestas_premiadas,
                archivo_aciertos_dbf = EXCLUDED.archivo_aciertos_dbf,
                cupones_ganadores_unicos = EXCLUDED.cupones_ganadores_unicos,
                cupones_ganadores_dbf = NULL,
                fecha_calculo = NOW()
            """,
            (
                fecha,
                turno,
                reporte["codigo_extracto"],
                reporte["sorteo"],
                reporte.get(
                    "cupones_jugados",
                    0,
                ),
                recaudacion,
                importe_premiados,
                comision,
                utilidad,
                porcentaje_utilidad,
                reporte.get(
                    "apuestas_premiadas",
                    0,
                ),
                reporte.get("archivo_aciertos_dbf"),
                cupones_ganadores_unicos,
            ),
        )

def obtener_turnos_calculados(
    conn: connection,
    fecha: int,
) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT
                TRIM(q.c_tsorteo)
            FROM premios p
            JOIN quiniela_exp q
                ON q.id = p.quiniela_exp_id
            WHERE p.fecha_sorteo = %s
            ORDER BY TRIM(q.c_tsorteo)
            """,
            (
                fecha,
            ),
        )

        return [
            row[0]
            for row in cur.fetchall()
        ]


def obtener_resumen_por_fecha(
    conn: connection,
    fecha: int,
) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                fecha_sorteo,
                turno,
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
                cupones_ganadores_dbf,
                fecha_calculo
            FROM resumen_auditoria
            WHERE fecha_sorteo = %s
            ORDER BY
                CASE turno
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M' THEN 3
                    WHEN 'V' THEN 4
                    WHEN 'N' THEN 5
                    ELSE 99
                END,
                codigo_extracto
            """,
            (
                fecha,
            ),
        )

        return cur.fetchall()