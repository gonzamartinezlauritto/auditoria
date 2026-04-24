import psycopg2
from config import DB_CONFIG

# =========================================================
# ELEGIR CASO DE PRUEBA
# =========================================================
CASO_ACTIVO = "previa_cuidad_20260312"

# =========================================================
# CASOS DE PRUEBA
# =========================================================
CASOS_PRUEBA = {

    "previa_cuidad_20260312": {
        "fecha": 20260312,
        "codigo_extracto": 51,
        "descripcion": "La Previa Cuidad B.A- 12/03/2026",
        "numeros": [
            "4162", "6470", "6973", "8417", "0166",
            "4840", "3857", "3866", "7330", "6115",
            "5125", "5013", "0088", "1603", "0627",
            "7347", "6596", "0772", "9723", "3320",
        ],
    },
    # Ejemplo de otro caso
    # "previa_ctes_20260312": {
    #     "fecha": 20260312,
    #   "codigo_extracto": 50,
    #    "descripcion": "La Previa Corrientes - 12/03/2026",
    #   "numeros": [
    #        "7461", "0449", "2375", "1440", "2430",
    #        "8926", "5819", "7932", "3214", "6317",
    #        "3905", "2047", "5761", "6340", "0062",
    #        "6567", "0574", "8389", "1354", "6432",
    #    ],
    # },
}


def normalizar_numero(numero: str) -> str:
    return str(numero).strip().zfill(4)


def main() -> None:
    print("===================================")
    print("CARGA DE RESULTADOS - PRUEBA")
    print("===================================")

    if CASO_ACTIVO not in CASOS_PRUEBA:
        print(f"Error: el caso '{CASO_ACTIVO}' no existe en CASOS_PRUEBA.")
        return

    caso = CASOS_PRUEBA[CASO_ACTIVO]

    fecha = int(caso["fecha"])
    codigo_extracto = int(caso["codigo_extracto"])
    descripcion = str(caso.get("descripcion", CASO_ACTIVO))
    numeros = [normalizar_numero(n) for n in caso["numeros"]]

    print(f"\nCaso activo: {CASO_ACTIVO}")
    print(f"Descripción: {descripcion}")
    print(f"Fecha: {fecha}")
    print(f"Código extracto: {codigo_extracto}")

    if len(numeros) != 20:
        print(f"\nError: el caso tiene {len(numeros)} números y deben ser exactamente 20.")
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # Verificar que exista el extracto
        cur.execute("""
            SELECT provincia, nombre_extracto
            FROM extractos
            WHERE codigo_extracto = %s
        """, (codigo_extracto,))
        extracto = cur.fetchone()

        if not extracto:
            print(f"\nError: no existe el código de extracto {codigo_extracto} en la tabla extractos.")
            return

        provincia, nombre_extracto = extracto
        print(f"Extracto encontrado: {provincia} - {nombre_extracto}")

        # Limpiar resultados previos de esa fecha/extracto
        cur.execute("""
            DELETE FROM resultados
            WHERE fecha_sorteo = %s
              AND codigo_extracto = %s
        """, (fecha, codigo_extracto))
        eliminados = cur.rowcount

        # Insertar los 20 resultados
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

        conn.commit()

        print("\n✔ Resultados cargados correctamente.")
        print(f"Resultados previos eliminados: {eliminados}")
        print("\nNúmeros cargados:")
        for orden, numero in enumerate(numeros, start=1):
            print(f"{orden:02d}. {numero}")

    except Exception as e:
        conn.rollback()
        print(f"\nError al cargar resultados de prueba: {e}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()