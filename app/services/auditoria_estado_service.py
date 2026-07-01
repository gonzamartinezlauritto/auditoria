from app.database import get_connection


def marcar_exp_cargado(conn, fecha: int, turno: str, archivo_exp: str):
    cur = conn.cursor()

    cur.execute("""
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
    """, (fecha, turno, archivo_exp))

    cur.close()


def marcar_dbf_cargado(conn, fecha: int, turno: str, archivo_dbf: str):
    cur = conn.cursor()

    cur.execute("""
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
    """, (fecha, turno, archivo_dbf))

    cur.close()


def marcar_resultados_cargados(conn, fecha: int, turno: str):
    cur = conn.cursor()

    cur.execute("""
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
    """, (fecha, turno))

    cur.close()


def marcar_calculo_ejecutado(conn, fecha: int, turno: str):
    cur = conn.cursor()

    cur.execute("""
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
    """, (fecha, turno))

    cur.close()


def obtener_estado_por_fecha(fecha: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
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
        """, (fecha,))

        rows = cur.fetchall()

        turnos = []

        for row in rows:
            (
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
                updated_at,
            ) = row

            turnos.append({
                "turno": turno,
                "exp_cargado": exp_cargado,
                "resultados_cargados": resultados_cargados,
                "dbf_cargado": dbf_cargado,
                "calculo_ejecutado": calculo_ejecutado,
                "archivo_exp": archivo_exp,
                "archivo_dbf": archivo_dbf,
                "fecha_exp": str(fecha_exp) if fecha_exp else None,
                "fecha_dbf": str(fecha_dbf) if fecha_dbf else None,
                "fecha_calculo": str(fecha_calculo) if fecha_calculo else None,
                "updated_at": str(updated_at) if updated_at else None,
            })

        return {
            "ok": True,
            "fecha": fecha,
            "turnos": turnos,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

    finally:
        cur.close()
        conn.close()