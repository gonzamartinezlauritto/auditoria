import psycopg2
from config import DB_CONFIG

SQL = """
INSERT INTO quiniela_exp (
    n_apues, n_maqre, n_agent, n_subag, n_maqui, n_cupon, n_linea,
    n_femis, c_hemis, c_ecupon, n_fsorteo, n_codlot, c_tsorteo,
    n_alcdes, n_alchas, c_nroapos, n_impapos, n_nodef, n_codext
)
SELECT
    r.n_apues,
    r.n_maqre,
    r.n_agent,
    r.n_subag,
    r.n_maqui,
    r.n_cupon,
    r.n_linea,
    r.n_femis,
    r.c_hemis,
    r.c_ecupon,
    r.n_fsorteo,
    r.n_codlot,
    r.c_tsorteo,
    r.n_alcdes,
    r.n_alchas,
    TRIM(r.c_nroapos),
    ROUND(r.n_impapos / 100.0, 2),
    r.n_nodef,
    r.n_codext
FROM quiniela_exp_raw r
JOIN extractos e
    ON e.codigo_extracto = r.n_codext;
"""

def main() -> None:
    conn = None
    cur = None

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM quiniela_exp_raw;")
        raw_count = cur.fetchone()[0]
        print(f"Registros en quiniela_exp_raw: {raw_count}")

        cur.execute("""
            SELECT COUNT(*)
            FROM quiniela_exp_raw r
            JOIN extractos e
              ON e.codigo_extracto = r.n_codext
        """)
        match_count = cur.fetchone()[0]
        print(f"Registros de raw que matchean con extractos: {match_count}")

        cur.execute(SQL)
        insertados = cur.rowcount

        conn.commit()

        print(f"Registros insertados en quiniela_exp: {insertados}")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error en process_exp.py: {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()