from pathlib import Path
import time
import psycopg2
from legacy.scripts_viejos.config import DB_CONFIG

FILE_PATH = Path("data/quiniela.exp")

COPY_SQL = """
COPY quiniela_exp_raw (
    n_apues, n_maqre, n_agent, n_subag, n_maqui,
    n_cupon, n_linea, n_femis, c_hemis, c_ecupon,
    n_fsorteo, n_codlot, c_tsorteo, n_alcdes, n_alchas,
    c_nroapos, n_impapos, n_nodef, n_codext
)
FROM STDIN
WITH (
    FORMAT csv,
    DELIMITER ',',
    QUOTE '"'
)
"""

def main() -> None:
    start = time.time()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    with FILE_PATH.open("r", encoding="utf-8", newline="") as file:
        cur.copy_expert(COPY_SQL, file)

    conn.commit()
    cur.close()
    conn.close()

    print(f"EXP cargado en raw. Tiempo: {time.time() - start:.2f} segundos")

if __name__ == "__main__":
    main()