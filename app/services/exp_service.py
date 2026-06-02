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
    turno = turno.upper().strip()

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            DELETE FROM premios p
            USING quiniela_exp q
            WHERE p.quiniela_exp_id = q.id
            AND q.n_fsorteo = %s
            AND TRIM(q.c_tsorteo) = %s
        """, (fecha, turno))

        premios_eliminados = cur.rowcount
        
        cur.execute("""
            DELETE FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND TRIM(c_tsorteo) = %s
        """, (fecha, turno))

        eliminados = cur.rowcount

        with file_path.open("r", encoding="utf-8", newline="") as file:
            cur.copy_expert(COPY_SQL, file)

        cur.execute("""
            SELECT COUNT(*)
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND TRIM(c_tsorteo) = %s
        """, (fecha, turno))

        cargados = cur.fetchone()[0] or 0

        if cargados == 0:
            raise Exception(
                f"No se encontraron filas para fecha={fecha}, turno={turno}"
            )

        conn.commit()

        return {
            "ok": True,
            "fecha": fecha,
            "turno": turno,
            "eliminados": eliminados,
            "cargados": cargados,
            "modo": "fast_copy_directo"
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