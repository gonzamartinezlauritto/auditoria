from decimal import Decimal, InvalidOperation
from pathlib import Path
import pandas as pd
import psycopg2
from legacy.scripts_viejos.config import DB_CONFIG

BASE_DIR = Path(__file__).parent
EXCEL_PATH = BASE_DIR / "data" / "cuponesGanadores20260312.xlsx"

def normalizar_decimal(valor) -> Decimal:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return Decimal("0.00")

    texto = str(valor).strip()
    if texto == "":
        return Decimal("0.00")

    # soporta "1.234,56" y "1234.56"
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return Decimal(texto).quantize(Decimal("0.01"))
    except InvalidOperation:
        return Decimal("0.00")


def leer_excel(path_excel: str, extracto_objetivo: int) -> pd.DataFrame:
    if not Path(path_excel).exists():
        raise FileNotFoundError(f"No existe el archivo: {path_excel}")

    df = pd.read_excel(path_excel)

    columnas = {c.upper().strip(): c for c in df.columns}

    requeridas = ["NUMERO", "EXTRACTO", "AP_ACIERTO", "IMPGANADO"]
    faltantes = [c for c in requeridas if c not in columnas]
    if faltantes:
        raise ValueError(f"Faltan columnas en Excel: {faltantes}. Columnas encontradas: {list(df.columns)}")

    df = df.rename(columns={
        columnas["NUMERO"]: "NUMERO",
        columnas["EXTRACTO"]: "EXTRACTO",
        columnas["AP_ACIERTO"]: "AP_ACIERTO",
        columnas["IMPGANADO"]: "IMPGANADO",
    })

    df["NUMERO"] = pd.to_numeric(df["NUMERO"], errors="coerce").fillna(0).astype(int)
    df["EXTRACTO"] = pd.to_numeric(df["EXTRACTO"], errors="coerce").fillna(0).astype(int)
    df["AP_ACIERTO"] = pd.to_numeric(df["AP_ACIERTO"], errors="coerce").fillna(0).astype(int)
    df["IMPGANADO_DEC"] = df["IMPGANADO"].apply(normalizar_decimal)

    df = df[df["EXTRACTO"] == extracto_objetivo].copy()

    # agrupación defensiva por si el Excel trae repetidos
    agrupado = (
        df.groupby(["NUMERO", "EXTRACTO"], as_index=False)
        .agg(
            AP_ACIERTO_EXCEL=("AP_ACIERTO", "sum"),
            IMPGANADO_EXCEL=("IMPGANADO_DEC", "sum"),
        )
    )

    return agrupado


def leer_postgres(fecha: int, extracto_objetivo: int) -> pd.DataFrame:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                q.n_cupon AS numero,
                q.n_codext AS extracto,
                COUNT(*) AS ap_acierto_pg,
                COALESCE(SUM(p.premio_total), 0) AS impganado_pg
            FROM premios p
            JOIN quiniela_exp q ON q.id = p.quiniela_exp_id
            WHERE p.fecha_sorteo = %s
              AND p.codigo_extracto = %s
              AND COALESCE(q.c_ecupon, '') <> 'A'
            GROUP BY q.n_cupon, q.n_codext
            ORDER BY q.n_cupon, q.n_codext
        """, (fecha, extracto_objetivo))

        rows = cur.fetchall()

        data = []
        for numero, extracto, ap_acierto_pg, impganado_pg in rows:
            data.append({
                "NUMERO": int(numero),
                "EXTRACTO": int(extracto),
                "AP_ACIERTO_PG": int(ap_acierto_pg),
                "IMPGANADO_PG": Decimal(str(impganado_pg)).quantize(Decimal("0.01")),
            })

        return pd.DataFrame(data)

    finally:
        cur.close()
        conn.close()


def comparar(fecha: int, extracto_objetivo: int, path_excel: str) -> None:
    df_excel = leer_excel(path_excel, extracto_objetivo)
    df_pg = leer_postgres(fecha, extracto_objetivo)

    comparado = df_excel.merge(
        df_pg,
        on=["NUMERO", "EXTRACTO"],
        how="outer"
    )

    comparado["AP_ACIERTO_EXCEL"] = comparado["AP_ACIERTO_EXCEL"].fillna(0).astype(int)
    comparado["AP_ACIERTO_PG"] = comparado["AP_ACIERTO_PG"].fillna(0).astype(int)
    comparado["IMPGANADO_EXCEL"] = comparado["IMPGANADO_EXCEL"].apply(
        lambda x: x if isinstance(x, Decimal) else Decimal("0.00")
    )
    comparado["IMPGANADO_PG"] = comparado["IMPGANADO_PG"].apply(
        lambda x: x if isinstance(x, Decimal) else Decimal("0.00")
    )

    comparado["DIF_ACIERTOS"] = comparado["AP_ACIERTO_EXCEL"] - comparado["AP_ACIERTO_PG"]
    comparado["DIF_IMPORTE"] = comparado["IMPGANADO_EXCEL"] - comparado["IMPGANADO_PG"]

    solo_excel = comparado[
        (comparado["AP_ACIERTO_EXCEL"] > 0) & (comparado["AP_ACIERTO_PG"] == 0)
    ].copy()

    solo_pg = comparado[
        (comparado["AP_ACIERTO_EXCEL"] == 0) & (comparado["AP_ACIERTO_PG"] > 0)
    ].copy()

    distintos = comparado[
        (comparado["AP_ACIERTO_EXCEL"] != comparado["AP_ACIERTO_PG"]) |
        (comparado["IMPGANADO_EXCEL"] != comparado["IMPGANADO_PG"])
    ].copy()

    print("===================================")
    print("COMPARACION EXCEL VS POSTGRES")
    print("===================================")
    print(f"Fecha: {fecha}")
    print(f"Extracto: {extracto_objetivo}")
    print()
    print(f"Registros Excel (cupón+extracto): {len(df_excel)}")
    print(f"Registros Postgres (cupón+extracto): {len(df_pg)}")
    print(f"Solo en Excel: {len(solo_excel)}")
    print(f"Solo en Postgres: {len(solo_pg)}")
    print(f"Con diferencias: {len(distintos)}")
    print()

    if len(solo_excel) > 0:
        print("=== CUPONES QUE ESTAN EN EXCEL Y NO EN POSTGRES ===")
        print(
            solo_excel[
                ["NUMERO", "EXTRACTO", "AP_ACIERTO_EXCEL", "IMPGANADO_EXCEL"]
            ]
            .sort_values(["EXTRACTO", "NUMERO"])
            .to_string(index=False)
        )
        print()

    if len(solo_pg) > 0:
        print("=== CUPONES QUE ESTAN EN POSTGRES Y NO EN EXCEL ===")
        print(
            solo_pg[
                ["NUMERO", "EXTRACTO", "AP_ACIERTO_PG", "IMPGANADO_PG"]
            ]
            .sort_values(["EXTRACTO", "NUMERO"])
            .to_string(index=False)
        )
        print()

    if len(distintos) > 0:
        print("=== CUPONES CON DIFERENCIAS ===")
        print(
            distintos[
                [
                    "NUMERO", "EXTRACTO",
                    "AP_ACIERTO_EXCEL", "AP_ACIERTO_PG", "DIF_ACIERTOS",
                    "IMPGANADO_EXCEL", "IMPGANADO_PG", "DIF_IMPORTE"
                ]
            ]
            .sort_values(["EXTRACTO", "NUMERO"])
            .to_string(index=False)
        )
        print()

    # Exporta para revisar cómodo
    out_path = Path("comparacion_excel_vs_pg_extracto.xlsx")
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        comparado.sort_values(["EXTRACTO", "NUMERO"]).to_excel(writer, index=False, sheet_name="comparado")
        solo_excel.sort_values(["EXTRACTO", "NUMERO"]).to_excel(writer, index=False, sheet_name="solo_excel")
        solo_pg.sort_values(["EXTRACTO", "NUMERO"]).to_excel(writer, index=False, sheet_name="solo_pg")
        distintos.sort_values(["EXTRACTO", "NUMERO"]).to_excel(writer, index=False, sheet_name="distintos")

    print(f"Archivo exportado: {out_path.resolve()}")


if __name__ == "__main__":
    fecha = 20260312
    extracto = 50
    comparar(fecha, extracto, EXCEL_PATH)