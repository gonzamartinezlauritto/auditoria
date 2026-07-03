import psycopg2
from legacy.scripts_viejos.config import DB_CONFIG


def obtener_nombre_extracto(cur, codigo_extracto: int) -> str:
    cur.execute("""
        SELECT provincia, nombre_extracto
        FROM extractos
        WHERE codigo_extracto = %s
    """, (codigo_extracto,))
    row = cur.fetchone()
    if not row:
        return ""
    provincia, nombre_extracto = row
    return f"{provincia} - {nombre_extracto}"


def cargar_resultados(fecha_sorteo: int, codigo_extracto: int, numeros: list[str]) -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for i, numero in enumerate(numeros, start=1):
        numero_formateado = str(numero).strip().zfill(4)

        cur.execute("""
            INSERT INTO resultados (
                fecha_sorteo,
                codigo_extracto,
                orden_resultado,
                numero_resultado
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (fecha_sorteo, codigo_extracto, orden_resultado)
            DO UPDATE SET numero_resultado = EXCLUDED.numero_resultado
        """, (fecha_sorteo, codigo_extracto, i, numero_formateado))

    conn.commit()
    cur.close()
    conn.close()


def main() -> None:
    print("===================================")
    print("CARGA DE RESULTADOS DE LOTERÍA")
    print("===================================")

    while True:
        fecha_sorteo = int(input("\nFecha del sorteo (YYYYMMDD): ").strip())
        codigo_extracto = int(input("Código de extracto/lotería: ").strip())

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        nombre = obtener_nombre_extracto(cur, codigo_extracto)
        cur.close()
        conn.close()

        if not nombre:
            print("No existe ese código de extracto.")
            continue

        print(f"Extracto seleccionado: {nombre}")

        print("\nIngresá los 20 números sorteados:")
        numeros = []

        for i in range(1, 21):
            while True:
                numero = input(f"Número {i}: ").strip()

                if not numero.isdigit():
                    print("El número debe ser numérico.")
                    continue

                if len(numero) > 4:
                    print("El número no puede tener más de 4 cifras.")
                    continue

                numeros.append(numero)
                break

        cargar_resultados(fecha_sorteo, codigo_extracto, numeros)

        print(f"\n✔ Resultados guardados correctamente para {nombre}.")

        continuar = input("\n¿Querés cargar otra lotería? (s/n): ").strip().lower()
        if continuar != "s":
            break

    print("\nProceso finalizado.")


if __name__ == "__main__":
    main()