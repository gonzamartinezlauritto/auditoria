from pathlib import Path
from decimal import Decimal

from dbfread import DBF

from app.database import get_connection
from app.services.auditoria_estado_service import marcar_dbf_cargado

def to_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except:
        return None


def to_decimal(value):
    if value in (None, ""):
        return Decimal("0.00")
    try:
        return Decimal(str(value))
    except:
        return Decimal("0.00")


def process_dbf(file_path: Path, fecha: int, turno: str):
    turno = turno.upper().strip()

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            DELETE FROM aciertos_dbf
            WHERE fecha_sorteo = %s
              AND turno = %s
        """, (fecha, turno))

        table = DBF(file_path, encoding="latin1")

        insertados = 0

        for row in table:
            cur.execute("""
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
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                fecha,
                turno,
                to_int(row.get("EXTRACTO")),
                to_int(row.get("AGENCIA")),
                to_int(row.get("SUBAGENCIA")),
                to_int(row.get("NROMAQUINA")),
                to_int(row.get("NUMERO")),
                to_int(row.get("APUESTAS")),
                to_int(row.get("AP_ACIERTO")),
                to_decimal(row.get("APOSTADO")),
                to_decimal(row.get("IMPGANADO")),
            ))

            insertados += 1

        cur.execute("""
            SELECT
                codigo_extracto,
                COUNT(*)
            FROM aciertos_dbf
            WHERE fecha_sorteo = %s
              AND turno = %s
            GROUP BY codigo_extracto
            ORDER BY codigo_extracto
        """, (fecha, turno))

        extractos = cur.fetchall()

        resumen = [
            {
                "codigo_extracto": r[0],
                "cantidad": r[1]
            }
            for r in extractos
        ]

        cur.execute("""
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
        """, (fecha, turno))

        unicos = cur.fetchone()[0]

        marcar_dbf_cargado(
            conn=conn,
            fecha=fecha,
            turno=turno,
            archivo_dbf=file_path.name
        )

        conn.commit()

        return {
            "ok": True,
            "filas_insertadas": insertados,
            "extractos": resumen,
            "cupones_ganadores_unicos": unicos,
        }

    except Exception as e:
        conn.rollback()
        return {
            "ok": False,
            "error": str(e)
        }

    finally:
        cur.close()
        conn.close()  