from pathlib import Path
from decimal import Decimal

import psycopg2
from dbfread import DBF

from config import DB_CONFIG

# ============================================
# CONFIG
# ============================================

FECHA = 20260513

DOWNLOADS_DIR = Path.home() / "Downloads"

# ============================================
# HELPERS
# ============================================

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


# ============================================
# MAIN
# ============================================

def main():

    print("====================================")
    print("CARGA ACIERTOS DBF")
    print("====================================")

    # ============================================
    # BUSCAR ÚLTIMO DBF EN DESCARGAS
    # ============================================

    dbf_files = list(DOWNLOADS_DIR.glob("*.dbf"))

    if not dbf_files:
        print("ERROR: No se encontraron archivos DBF en Descargas")
        return

    ultimo_dbf = max(
        dbf_files,
        key=lambda f: f.stat().st_mtime
    )

    print(f"\nDBF encontrado:")
    print(ultimo_dbf)

    # ============================================
    # LEER DBF
    # ============================================

    table = DBF(
        ultimo_dbf,
        encoding="latin1"
    )

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:

        # ============================================
        # LIMPIAR FECHA
        # ============================================

        cur.execute("""
            DELETE FROM aciertos_dbf
            WHERE fecha_sorteo = %s
        """, (FECHA,))

        eliminados = cur.rowcount

        print(f"\nRegistros eliminados: {eliminados}")

        # ============================================
        # INSERTAR
        # ============================================

        insertados = 0

        for row in table:

            cur.execute("""
                INSERT INTO aciertos_dbf (
                    fecha_sorteo,
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
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                FECHA,
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

            if insertados % 1000 == 0:
                print(f"Insertados: {insertados}")

        conn.commit()

        print("\n====================================")
        print("DBF CARGADO CORRECTAMENTE")
        print("====================================")

        print(f"Filas insertadas: {insertados}")

        # ============================================
        # TOTALES POR EXTRACTO
        # ============================================

        print("\n====================================")
        print("TOTALES POR EXTRACTO")
        print("====================================")

        cur.execute("""
            SELECT
                codigo_extracto,
                COUNT(*) AS cantidad
            FROM aciertos_dbf
            WHERE fecha_sorteo = %s
            GROUP BY codigo_extracto
            ORDER BY codigo_extracto
        """, (FECHA,))

        rows = cur.fetchall()

        for row in rows:
            print(
                f"Extracto {row[0]} => {row[1]}"
            )

        # ============================================
        # CUPONES GANADORES ÚNICOS
        # ============================================

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
                GROUP BY
                    agencia,
                    subagencia,
                    nromaquina,
                    numero
            ) t
        """, (FECHA,))

        cupones_unicos = cur.fetchone()[0]

        print("\n====================================")
        print("CUPONES GANADORES ÚNICOS")
        print("====================================")

        print(cupones_unicos)

    except Exception as e:

        conn.rollback()

        print("\nERROR:")
        print(e)

    finally:

        cur.close()
        conn.close()


if __name__ == "__main__":
    main()