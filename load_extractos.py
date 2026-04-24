from pathlib import Path
import pandas as pd
import psycopg2
from config import DB_CONFIG

FILE_PATH = Path("data/paramqla.xlsx")

def main() -> None:
    df = pd.read_excel(FILE_PATH)

    df = df.rename(columns={
        "CODIGO EXTRACTO": "codigo_extracto",
        "NRO EVENTO": "nro_evento",
        "COD PROVINCIA": "cod_provincia",
        "PROVINCIA": "provincia",
        "NOMBRE EXTRACTO": "nombre_extracto",
        "HORA INICIO": "hora_inicio",
        "CANT. CIFRAS": "cant_cifras",
        "4 CIFRAS": "premio_4_cifras",
        "3 CIFRAS": "premio_3_cifras",
        "2 CIFRAS": "premio_2_cifras",
        "1 CIFRA": "premio_1_cifra",
        "CEXTARCH": "cextarch",
        "CEVENTOCOM": "ceventocom",
        "CANT. EXTRACCIONES": "cant_extracciones",
        "TOPE REDOBLONA": "tope_redoblona",
        "IACTIVADO": "activado",
        "APROXIMACION 4 CIFRAS": "aprox_4_cifras",
        "APROXIMACION 3 CIFRAS": "aprox_3_cifras",
        "IORDENPROV": "orden_provincia",
    })

    columnas = [
        "codigo_extracto", "nro_evento", "cod_provincia", "provincia",
        "nombre_extracto", "hora_inicio", "cant_cifras",
        "premio_4_cifras", "premio_3_cifras", "premio_2_cifras", "premio_1_cifra",
        "cextarch", "ceventocom","cant_extracciones","tope_redoblona","activado",
        "aprox_4_cifras","aprox_3_cifras","orden_provincia"
    ]

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("DELETE FROM extractos;")

    for _, row in df[columnas].iterrows():
        cur.execute("""
            INSERT INTO extractos (
                codigo_extracto, nro_evento, cod_provincia, provincia,
                nombre_extracto, hora_inicio, cant_cifras,
                premio_4_cifras, premio_3_cifras, premio_2_cifras, premio_1_cifra,
                cextarch, ceventocom,cant_extracciones,tope_redoblona,activado,
                aprox_4_cifras,aprox_3_cifras,orden_provincia
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, tuple(row))

    conn.commit()
    cur.close()
    conn.close()

    print("Extractos cargados correctamente.")

if __name__ == "__main__":
    main()