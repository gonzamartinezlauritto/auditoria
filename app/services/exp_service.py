from pathlib import Path
import subprocess

from app.database import get_connection

COPY_SQL = """
COPY quiniela_exp (
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

def process_exp(file_path: Path, fecha: int, turno: str):

    pasos = []
    turno = turno.upper()

    try:

        subprocess.run(
            ["python", "load_exp_raw.py", str(file_path)],
            check=True
        )
        pasos.append("load_exp_raw OK")

        subprocess.run(
            ["python", "process_exp.py"],
            check=True
        )
        pasos.append("process_exp OK")

        subprocess.run(
            ["python", "load_quiniela.py", str(file_path), str(fecha), turno],
            check=True
        )
        pasos.append("load_quiniela OK")

        # =====================================
        # VALIDAR CARGA POR FECHA + TURNO
        # =====================================

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT COUNT(*)
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND c_tsorteo = %s
        """, (fecha, turno))

        cantidad = cur.fetchone()[0] or 0

        cur.close()
        conn.close()

        if cantidad == 0:
            return {
                "ok": False,
                "pasos": pasos,
                "error": f"No se encontraron apuestas para fecha {fecha} y turno {turno}. Verificar archivo EXP."
            }

        pasos.append("validacion fecha/turno OK")

        return {
            "ok": True,
            "fecha": fecha,
            "turno": turno,
            "apuestas_cargadas": cantidad,
            "pasos": pasos
        }

    except subprocess.CalledProcessError as e:

        return {
            "ok": False,
            "error": str(e),
            "pasos": pasos
        }

    except Exception as e:

        return {
            "ok": False,
            "error": str(e),
            "pasos": pasos
        }

def process_exp_fast(file_path: Path, fecha: int, turno: str):
    archivo_origen = file_path.name
    turno = turno.upper().strip()

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
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
            ) ON COMMIT DROP;
        """)

        copy_tmp_sql = """
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

        with file_path.open("r", encoding="utf-8", newline="") as file:
            cur.copy_expert(copy_tmp_sql, file)

        cur.execute("""
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
                TRIM(c_tsorteo),
                n_alcdes,
                n_alchas,
                c_nroapos,
                n_impapos,
                n_nodef,
                n_codext,
                %s,
                NOW()
            FROM quiniela_exp_tmp
            ON CONFLICT DO NOTHING
        """, (archivo_origen,))

        insertados = cur.rowcount

        cur.execute("""
            SELECT COUNT(*)
            FROM quiniela_exp_tmp
        """)
        total_archivo = cur.fetchone()[0] or 0

        ignorados = total_archivo - insertados

        cur.execute("""
            INSERT INTO cargas_exp (
                archivo_origen,
                fecha_archivo
            )
            VALUES (%s, %s)
            ON CONFLICT (archivo_origen)
            DO UPDATE SET fecha_carga = NOW()
        """, (archivo_origen, fecha))

        cur.execute("""
            SELECT COUNT(*)
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND TRIM(c_tsorteo) = %s
        """, (fecha, turno))

        cargados_turno = cur.fetchone()[0] or 0

        if cargados_turno == 0:
            raise Exception(
                f"El archivo se cargó, pero no hay datos para fecha={fecha}, turno={turno}"
            )

        conn.commit()

        return {
            "ok": True,
            "archivo_origen": archivo_origen,
            "fecha": fecha,
            "turno": turno,
            "total_archivo": total_archivo,
            "insertados": insertados,
            "ignorados_por_duplicado": ignorados,
            "cargados_turno": cargados_turno,
            "modo": "copy_tmp_insert_on_conflict_do_nothing"
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
