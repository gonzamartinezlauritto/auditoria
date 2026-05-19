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


def mostrar_preview_archivo():
    print("\n==============================")
    print("PREVIEW ARCHIVO")
    print("==============================")
    print("Ruta:", FILE_PATH.resolve())

    with FILE_PATH.open("r", encoding="utf-8", newline="") as f:
        for i in range(5):
            linea = f.readline().strip()
            if not linea:
                break
            print(f"[{i+1}] {linea}")


def mostrar_resumen_cargas(cur):
    cur.execute("""
        SELECT
            n_fsorteo,
            n_femis,
            n_codext,
            COUNT(*) AS cantidad
        FROM quiniela_exp
        GROUP BY n_fsorteo, n_femis, n_codext
        ORDER BY n_fsorteo DESC, n_codext
        LIMIT 50
    """)

    rows = cur.fetchall()

    print("\n==============================")
    print("RESUMEN FECHAS CARGADAS")
    print("==============================")

    for row in rows:
        print(row)


def mostrar_ultimas_apuestas(cur):
    cur.execute("""
        SELECT
            n_fsorteo,
            n_codext,
            n_agent,
            n_subag,
            n_maqui,
            n_cupon,
            c_nroapos,
            n_impapos
        FROM quiniela_exp
        ORDER BY id DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    print("\n==============================")
    print("ÚLTIMAS APUESTAS INSERTADAS")
    print("==============================")

    for row in rows:
        print(row)


def main() -> None:
    if not FILE_PATH.exists():
        print(f"No se encontró el archivo: {FILE_PATH.resolve()}")
        return

    mostrar_preview_archivo()

    start_time = time.time()

    conn = None
    cur = None

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("\n==============================")
        print("INICIANDO CARGA")
        print("==============================")

        with FILE_PATH.open("r", encoding="utf-8", newline="") as file:
            cur.copy_expert(COPY_SQL, file)

        conn.commit()

        end_time = time.time()
        duration = end_time - start_time

        print("\n==============================")
        print("CARGA COMPLETADA")
        print("==============================")

        print(f"Tiempo total: {duration:.2f} segundos")

        mostrar_resumen_cargas(cur)
        mostrar_ultimas_apuestas(cur)

        # Validación rápida:
        cur.execute("""
            SELECT
                MAX(n_fsorteo)
            FROM quiniela_exp
        """)

        ultima_fecha = cur.fetchone()[0]

        print("\n==============================")
        print("ÚLTIMA FECHA DETECTADA")
        print("==============================")
        print(ultima_fecha)

    except Exception as error:
        if conn:
            conn.rollback()

        print("\n==============================")
        print("ERROR")
        print("==============================")
        print(error)

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


if __name__ == "__main__":
    main()