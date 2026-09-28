from psycopg2.extensions import connection


# =========================================================
# MARCAR EXP CARGADO
# =========================================================

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


# =========================================================
# MARCAR DBF CARGADO
# =========================================================

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


# =========================================================
# MARCAR RESULTADOS CARGADOS
# =========================================================

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


# =========================================================
# MARCAR CÁLCULO EJECUTADO
# =========================================================

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


# =========================================================
# MARCAR COMPARACIÓN EJECUTADA
# =========================================================

def marcar_comparacion_ejecutada(
    conn: connection,
    fecha: int,
    turno: str,
    hay_diferencias: bool,
) -> None:
    """
    Marca la comparación Sistema/DBF como ejecutada y guarda
    el resultado general de la comparación.

    hay_diferencias:
        False -> comparación ejecutada sin diferencias relevantes.
        True  -> comparación ejecutada con diferencias relevantes.
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE auditoria_cargas
            SET
                comparacion_ejecutada = TRUE,
                fecha_comparacion = NOW(),
                hay_diferencias = %s,
                updated_at = NOW()
            WHERE fecha_sorteo = %s
              AND turno = %s
            """,
            (
                hay_diferencias,
                fecha,
                turno,
            ),
        )


# =========================================================
# INVALIDAR COMPARACIÓN
# =========================================================

def invalidar_comparacion(
    conn: connection,
    fecha: int,
    turno: str,
) -> None:
    """
    Invalida la comparación anterior.

    Al dejar de existir una comparación vigente,
    hay_diferencias vuelve a NULL.
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE auditoria_cargas
            SET
                comparacion_ejecutada = FALSE,
                fecha_comparacion = NULL,
                hay_diferencias = NULL,
                updated_at = NOW()
            WHERE fecha_sorteo = %s
              AND turno = %s
            """,
            (
                fecha,
                turno,
            ),
        )


# =========================================================
# INVALIDAR CÁLCULO Y COMPARACIÓN
# =========================================================

def invalidar_calculo_y_comparacion(
    conn: connection,
    fecha: int,
    turno: str,
) -> None:
    """
    Invalida tanto el cálculo como la comparación.

    Si el cálculo deja de ser válido, cualquier comparación
    realizada sobre ese cálculo también deja de ser válida.
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE auditoria_cargas
            SET
                calculo_ejecutado = FALSE,
                fecha_calculo = NULL,
                comparacion_ejecutada = FALSE,
                fecha_comparacion = NULL,
                hay_diferencias = NULL,
                updated_at = NOW()
            WHERE fecha_sorteo = %s
              AND turno = %s
            """,
            (
                fecha,
                turno,
            ),
        )


# =========================================================
# OBTENER ESTADO POR FECHA
# =========================================================

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

                comparacion_ejecutada,
                fecha_comparacion,
                hay_diferencias,

                evento_cerrado,
                fecha_cierre,
                cerrado_por,

                fecha_reapertura,
                reabierto_por,
                motivo_reapertura,

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


# =========================================================
# OBTENER EVENTO ESPECÍFICO
# =========================================================

def obtener_evento(
    conn: connection,
    fecha: int,
    turno: str,
):
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

                comparacion_ejecutada,
                hay_diferencias,
                evento_cerrado,

                fecha_comparacion,

                fecha_cierre,
                cerrado_por,

                fecha_reapertura,
                reabierto_por,
                motivo_reapertura

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


# =========================================================
# CERRAR EVENTO
# =========================================================

def cerrar_evento(
    conn: connection,
    fecha: int,
    turno: str,
    usuario: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE auditoria_cargas
            SET
                evento_cerrado = TRUE,
                fecha_cierre = NOW(),
                cerrado_por = %s,
                updated_at = NOW()
            WHERE fecha_sorteo = %s
              AND turno = %s
            """,
            (
                usuario,
                fecha,
                turno,
            ),
        )


# =========================================================
# REABRIR EVENTO
# =========================================================

def reabrir_evento(
    conn: connection,
    fecha: int,
    turno: str,
    usuario: str,
    motivo: str,
) -> None:
    """
    Reabre un evento cerrado.

    La comparación anterior deja de considerarse vigente,
    por lo que:
        comparacion_ejecutada = FALSE
        fecha_comparacion = NULL
        hay_diferencias = NULL

    El cálculo realizado se conserva.
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE auditoria_cargas
            SET
                evento_cerrado = FALSE,

                fecha_reapertura = NOW(),
                reabierto_por = %s,
                motivo_reapertura = %s,

                comparacion_ejecutada = FALSE,
                fecha_comparacion = NULL,
                hay_diferencias = NULL,

                updated_at = NOW()

            WHERE fecha_sorteo = %s
              AND turno = %s
            """,
            (
                usuario,
                motivo,
                fecha,
                turno,
            ),
        )


# =========================================================
# REGISTRAR HISTORIAL DEL EVENTO
# =========================================================

def registrar_historial_evento(
    conn: connection,
    fecha: int,
    turno: str,
    accion: str,
    usuario: str,
    motivo: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO auditoria_eventos_historial (
                fecha_sorteo,
                turno,
                accion,
                usuario,
                motivo,
                created_at
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                NOW()
            )
            """,
            (
                fecha,
                turno,
                accion,
                usuario,
                motivo,
            ),
        )


# =========================================================
# OBTENER HISTORIAL DEL EVENTO
# =========================================================

def obtener_historial_evento(
    conn: connection,
    fecha: int,
    turno: str,
) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
                fecha_sorteo,
                turno,
                accion,
                usuario,
                motivo,
                created_at

            FROM auditoria_eventos_historial

            WHERE fecha_sorteo = %s
              AND turno = %s

            ORDER BY
                created_at DESC,
                id DESC
            """,
            (
                fecha,
                turno,
            ),
        )

        return cur.fetchall()