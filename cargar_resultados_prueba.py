import psycopg2
from config import DB_CONFIG

CASO_ACTIVO = "previa_20260513_todos"

CASOS_PRUEBA = {
    "previa_20260513_todos": [
        {
            "fecha": 20260513,
            "codigo_extracto": 50,
            "descripcion": "Correntina - La Previa - 13/05/2026",
            "numeros": [
                "8893", "0228", "9941", "1443", "6222",
                "5745", "4685", "9658", "8633", "8614",
                "9291", "3410", "4608", "1038", "7536",
                "1210", "3851", "5310", "1033", "1221",
            ],
        },
        {
            "fecha": 20260513,
            "codigo_extracto": 51,
            "descripcion": "Ciudad B.A. - La Previa - 13/05/2026",
            "numeros": [
                "0610", "1629", "7503", "6796", "6380",
                "0103", "9185", "2439", "7844", "4477",
                "1569", "8147", "3783", "4319", "4718",
                "6563", "1482", "9956", "1876", "7181",
            ],
        },
        {
            "fecha": 20260513,
            "codigo_extracto": 52,
            "descripcion": "Bonaerense - La Previa - 13/05/2026",
            "numeros": [
                "2047", "4568", "3412", "4705", "7018",
                "6011", "9187", "6636", "7315", "6251",
                "9936", "1993", "7002", "9671", "8404",
                "7325", "8508", "6983", "2074", "9589",
            ],
        },
        {
            "fecha": 20260513,
            "codigo_extracto": 53,
            "descripcion": "Santa Fe - La Previa - 13/05/2026",
            "numeros": [
                "3017", "2277", "3694", "0450", "7322",
                "9611", "7701", "2362", "3289", "0267",
                "3145", "7763", "5353", "2480", "4994",
                "4593", "9055", "5479", "1597", "1400",
            ],
        },
        {
            "fecha": 20260513,
            "codigo_extracto": 54,
            "descripcion": "Córdoba - La Previa - 13/05/2026",
            "numeros": [
                "2944", "7614", "0369", "7526", "3592",
                "5082", "2923", "7382", "9057", "5471",
                "3815", "2276", "2395", "1120", "2238",
                "3105", "9829", "2399", "1388", "7576",
            ],
        },
        {
            "fecha": 20260513,
            "codigo_extracto": 55,
            "descripcion": "Entre Ríos - La Previa - 13/05/2026",
            "numeros": [
                "1966", "8107", "9683", "2957", "4805",
                "6995", "3794", "9631", "2406", "3850",
                "4592", "9819", "3052", "3294", "9484",
                "9943", "9099", "3786", "0448", "3993",
            ],
        },
        {
            "fecha": 20260513,
            "codigo_extracto": 56,
            "descripcion": "Chaco - La Previa - 13/05/2026",
            "numeros": [
                "9382", "4628", "1968", "3057", "3264",
                "7509", "2863", "3313", "0084", "2929",
                "6583", "9899", "6951", "3878", "5387",
                "0471", "5125", "4150", "1822", "6228",
            ],
        },
    ],
}


def normalizar_numero(numero: str) -> str:
    return str(numero).strip().zfill(4)


def cargar_caso(cur, caso: dict) -> None:
    fecha = int(caso["fecha"])
    codigo_extracto = int(caso["codigo_extracto"])
    descripcion = str(caso.get("descripcion", "Sin descripción"))
    numeros = [normalizar_numero(n) for n in caso["numeros"]]

    print("\n===================================")
    print(f"Cargando: {descripcion}")
    print(f"Fecha: {fecha}")
    print(f"Extracto: {codigo_extracto}")

    if len(numeros) != 20:
        raise ValueError(
            f"El extracto {codigo_extracto} tiene {len(numeros)} números. Deben ser 20."
        )

    cur.execute("""
        SELECT provincia, nombre_extracto
        FROM extractos
        WHERE codigo_extracto = %s
    """, (codigo_extracto,))
    extracto = cur.fetchone()

    if not extracto:
        raise ValueError(f"No existe el extracto {codigo_extracto} en la tabla extractos.")

    provincia, nombre_extracto = extracto
    print(f"Extracto encontrado: {provincia} - {nombre_extracto}")

    cur.execute("""
        DELETE FROM resultados
        WHERE fecha_sorteo = %s
          AND codigo_extracto = %s
    """, (fecha, codigo_extracto))
    eliminados = cur.rowcount

    for orden, numero in enumerate(numeros, start=1):
        cur.execute("""
            INSERT INTO resultados (
                fecha_sorteo,
                codigo_extracto,
                orden_resultado,
                numero_resultado
            )
            VALUES (%s, %s, %s, %s)
        """, (fecha, codigo_extracto, orden, numero))

    print(f"Resultados previos eliminados: {eliminados}")
    print("Números cargados:")
    for orden, numero in enumerate(numeros, start=1):
        print(f"{orden:02d}. {numero}")


def main() -> None:
    print("===================================")
    print("CARGA DE RESULTADOS")
    print("===================================")

    if CASO_ACTIVO not in CASOS_PRUEBA:
        print(f"Error: el caso '{CASO_ACTIVO}' no existe.")
        return

    casos = CASOS_PRUEBA[CASO_ACTIVO]

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        for caso in casos:
            cargar_caso(cur, caso)

        conn.commit()

        print("\n===================================")
        print("✔ TODOS LOS RESULTADOS FUERON CARGADOS")
        print("===================================")

    except Exception as e:
        conn.rollback()
        print("\nERROR:")
        print(e)

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()