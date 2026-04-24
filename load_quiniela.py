from pathlib import Path
import psycopg2
import time

DB_CONFIG = {
    "host": "localhost",
    "dbname": "quiniela_db",
    "user": "postgres",
    "password": "loteria",
    "port": 5432,
}

FILE_PATH = Path("data/quiniela.exp")

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

def main() -> None:
    if not FILE_PATH.exists():
        print(f"No se encontró el archivo: {FILE_PATH.resolve()}")
        return

    start_time = time.time()

    conn = None
    cur = None

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("Iniciando carga...")

        with FILE_PATH.open("r", encoding="utf-8", newline="") as file:
            cur.copy_expert(COPY_SQL, file)

        conn.commit()

        end_time = time.time()
        duration = end_time - start_time

        print("Carga completada correctamente.")
        print(f"Tiempo total: {duration:.2f} segundos")

    except Exception as error:
        if conn:
            conn.rollback()
        print(f"Error durante la carga: {error}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()