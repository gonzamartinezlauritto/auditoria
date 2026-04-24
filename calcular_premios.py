import psycopg2
from config import DB_CONFIG

def comparar(apuesta: str, resultado: str) -> int:
    a = apuesta.strip()
    r = resultado.strip().zfill(4)

    if len(a) == 4 and a == r:
        return 4
    if len(a) == 3 and a == r[-3:]:
        return 3
    if len(a) == 2 and a == r[-2:]:
        return 2
    if len(a) == 1 and a == r[-1:]:
        return 1
    return 0

def obtener_multiplicador(cifras: int, extracto: dict) -> int:
    if cifras == 4:
        return extracto["premio_4_cifras"]
    if cifras == 3:
        return extracto["premio_3_cifras"]
    if cifras == 2:
        return extracto["premio_2_cifras"]
    if cifras == 1:
        return extracto["premio_1_cifra"]
    return 0

def main(fecha_sorteo: int, codigo_extracto: int) -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT premio_4_cifras, premio_3_cifras, premio_2_cifras, premio_1_cifra
        FROM extractos
        WHERE codigo_extracto = %s
    """, (codigo_extracto,))
    row = cur.fetchone()

    if not row:
        print("No existe extracto.")
        return

    extracto = {
        "premio_4_cifras": row[0],
        "premio_3_cifras": row[1],
        "premio_2_cifras": row[2],
        "premio_1_cifra": row[3],
    }

    cur.execute("""
        SELECT id, c_nroapos, n_impapos
        FROM quiniela_exp
        WHERE n_fsorteo = %s AND n_codext = %s
    """, (fecha_sorteo, codigo_extracto))
    apuestas = cur.fetchall()

    cur.execute("""
        SELECT orden_resultado, numero_resultado
        FROM resultados
        WHERE fecha_sorteo = %s AND codigo_extracto = %s
        ORDER BY orden_resultado
    """, (fecha_sorteo, codigo_extracto))
    resultados = cur.fetchall()

    for apuesta_id, numero_apostado, importe in apuestas:
        for orden, numero_resultado in resultados:
            cifras = comparar(numero_apostado, numero_resultado)

            if cifras > 0:
                multiplicador = obtener_multiplicador(cifras, extracto)
                premio_total = importe * multiplicador

                cur.execute("""
                    INSERT INTO premios (
                        quiniela_exp_id, fecha_sorteo, codigo_extracto,
                        numero_apostado, numero_resultado, orden_resultado,
                        cifras_acertadas, importe_apostado, multiplicador, premio_total
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    apuesta_id, fecha_sorteo, codigo_extracto,
                    numero_apostado.strip(), numero_resultado, orden,
                    cifras, importe, multiplicador, premio_total
                ))

                break

    conn.commit()
    cur.close()
    conn.close()
    print("Premios calculados correctamente.")

if __name__ == "__main__":
    main(fecha_sorteo=20260304, codigo_extracto=50)