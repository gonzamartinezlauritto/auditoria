import psycopg2
from config import DB_CONFIG

def cargar_resultados(fecha_sorteo: int, codigo_extracto: int, numeros: list[str]) -> None:
    if len(numeros) != 20:
        raise ValueError("Se deben informar exactamente 20 números.")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for i, numero in enumerate(numeros, start=1):
        numero_formateado = str(numero).strip().zfill(4)

        cur.execute("""
            INSERT INTO resultados (fecha_sorteo, codigo_extracto, orden_resultado, numero_resultado)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (fecha_sorteo, codigo_extracto, orden_resultado)
            DO UPDATE SET numero_resultado = EXCLUDED.numero_resultado
        """, (fecha_sorteo, codigo_extracto, i, numero_formateado))

    conn.commit()
    cur.close()
    conn.close()

    print(f"Resultados cargados correctamente para extracto {codigo_extracto}.")