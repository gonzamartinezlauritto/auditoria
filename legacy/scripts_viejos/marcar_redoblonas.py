import psycopg2
from legacy.scripts_viejos.config import DB_CONFIG


def main() -> None:
    fecha = int(input("Fecha (YYYYMMDD): ").strip())
    codigo_extracto = int(input("Extracto: ").strip())

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # Limpiar marcas previas solo para esa fecha/extracto
        cur.execute("""
            UPDATE quiniela_exp
            SET
                es_redoblona_base = FALSE,
                es_redoblona_detalle = FALSE,
                linea_base_id = NULL,
                redoblona_grupo = NULL
            WHERE n_fsorteo = %s
              AND n_codext = %s
        """, (fecha, codigo_extracto))

        cur.execute("""
            SELECT
                id,
                n_apues,
                n_cupon,
                n_linea,
                c_nroapos,
                n_impapos,
                c_ecupon
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND n_codext = %s
              AND COALESCE(c_ecupon, '') <> 'A'
            ORDER BY id
        """, (fecha, codigo_extracto))

        rows = cur.fetchall()

        registros = [
            {
                "id": r[0],
                "n_apues": r[1],
                "n_cupon": r[2],
                "n_linea": r[3],
                "c_nroapos": str(r[4]).strip(),
                "n_impapos": float(r[5]) if r[5] is not None else 0.0,
                "c_ecupon": r[6],
            }
            for r in rows
        ]

        grupo = 1
        bases = 0
        detalles = 0

        i = 0
        while i < len(registros):
            actual = registros[i]
            siguiente = registros[i + 1] if i + 1 < len(registros) else None

            if actual["n_impapos"] <= 0:
                i += 1
                continue

            es_redoblona = (
                siguiente is not None
                and actual["n_apues"] == siguiente["n_apues"]
                and actual["n_cupon"] == siguiente["n_cupon"]
                and siguiente["n_linea"] == actual["n_linea"] + 1
                and siguiente["n_impapos"] == 0.0
            )

            if es_redoblona:
                cur.execute("""
                    UPDATE quiniela_exp
                    SET
                        es_redoblona_base = TRUE,
                        redoblona_grupo = %s
                    WHERE id = %s
                """, (grupo, actual["id"]))

                cur.execute("""
                    UPDATE quiniela_exp
                    SET
                        es_redoblona_detalle = TRUE,
                        linea_base_id = %s,
                        redoblona_grupo = %s
                    WHERE id = %s
                """, (actual["id"], grupo, siguiente["id"]))

                bases += 1
                detalles += 1
                grupo += 1
                i += 2
            else:
                i += 1

        conn.commit()

        print("\nMarcas aplicadas correctamente.")
        print(f"Redoblonas base: {bases}")
        print(f"Redoblonas detalle: {detalles}")
        print(f"Grupos creados: {grupo - 1}")

    except Exception as e:
        conn.rollback()
        print(f"\nError: {e}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()