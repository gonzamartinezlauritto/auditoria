from pathlib import Path
import sys
import psycopg2
import time

DB_CONFIG = {
    "host": "localhost",
    "dbname": "quiniela_db",
    "user": "postgres",
    "password": "loteria",
    "port": 5432,
}


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


def mostrar_preview_archivo(file_path: Path):
    print("\n==============================")
    print("PREVIEW ARCHIVO")
    print("==============================")
    print("Ruta:", file_path.resolve())

    with file_path.open("r", encoding="utf-8", newline="") as f:
        for i in range(5):
            linea = f.readline().strip()
            if not linea:
                break
            print(f"[{i + 1}] {linea}")


def mostrar_resumen_fecha_turno(cur, fecha: int, turno: str):
    cur.execute("""
        SELECT
            n_fsorteo,
            TRIM(c_tsorteo) AS turno,
            n_codext,
            COUNT(*) AS cantidad
        FROM quiniela_exp
        WHERE n_fsorteo = %s
          AND TRIM(c_tsorteo) = %s
        GROUP BY n_fsorteo, TRIM(c_tsorteo), n_codext
        ORDER BY n_codext
    """, (fecha, turno))

    rows = cur.fetchall()

    print("\n==============================")
    print("RESUMEN CARGA FECHA/TURNO")
    print("==============================")

    total = 0

    for row in rows:
        print(row)
        total += row[3]

    print(f"TOTAL FILAS FECHA/TURNO: {total}")

    return total


def mostrar_fechas_turnos_detectados(cur):
    cur.execute("""
        SELECT
            n_fsorteo,
            TRIM(c_tsorteo) AS turno,
            COUNT(*) AS cantidad
        FROM quiniela_exp
        GROUP BY n_fsorteo, TRIM(c_tsorteo)
        ORDER BY n_fsorteo DESC, turno
        LIMIT 20
    """)

    print("\n==============================")
    print("FECHAS/TURNOS DETECTADOS")
    print("==============================")

    for row in cur.fetchall():
        print(row)


def main() -> None:
    if len(sys.argv) < 4:
        print("Uso:")
        print("python load_quiniela.py <file_path> <fecha> <turno>")
        print("Ejemplo:")
        print("python load_quiniela.py uploads/quiniela.exp 20260529 PV")
        return

    file_path = Path(sys.argv[1])
    fecha = int(sys.argv[2])
    turno = str(sys.argv[3]).upper().strip()

    if not file_path.exists():
        print(f"No se encontró el archivo: {file_path.resolve()}")
        return

    mostrar_preview_archivo(file_path)

    start_time = time.time()

    conn = None
    cur = None

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        """
        print("\n==============================")
        print("LIMPIANDO CARGA ANTERIOR")
        print("==============================")

        cur.execute(
            DELETE FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND TRIM(c_tsorteo) = %s
        , (fecha, turno))

        eliminados = cur.rowcount

        print(f"Filas eliminadas para {fecha} / {turno}: {eliminados}")
        """
        print("\n==============================")
        print("INICIANDO CARGA")
        print("==============================")

        with file_path.open("r", encoding="utf-8", newline="") as file:
            cur.copy_expert(COPY_SQL, file)

        mostrar_fechas_turnos_detectados(cur)

        total_cargado = mostrar_resumen_fecha_turno(
            cur,
            fecha,
            turno
        )

        if total_cargado == 0:
            raise Exception(
                f"El archivo se cargó, pero no hay filas para fecha={fecha}, turno={turno}. "
                "Verificar que el EXP corresponda al turno indicado."
            )

        conn.commit()

        duration = time.time() - start_time

        print("\n==============================")
        print("CARGA COMPLETADA")
        print("==============================")
        print(f"Tiempo total: {duration:.2f} segundos")
        print(f"Filas cargadas fecha/turno: {total_cargado}")

    except Exception as error:
        if conn:
            conn.rollback()

        print("\n==============================")
        print("ERROR")
        print("==============================")
        print(error)

        raise

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


if __name__ == "__main__":
    main()