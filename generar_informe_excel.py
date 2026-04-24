from pathlib import Path

import pandas as pd
import psycopg2

from config import DB_CONFIG


def limpiar_nombre_archivo(texto: str) -> str:
    invalidos = '<>:"/\\|?*'
    resultado = texto
    for char in invalidos:
        resultado = resultado.replace(char, "_")
    return resultado.strip().replace(" ", "_")


def main() -> None:
    print("===================================")
    print("GENERAR INFORME EXCEL")
    print("===================================")

    fecha = int(input("\nFecha del sorteo (YYYYMMDD): ").strip())
    codigo_extracto = int(input("Código de extracto/lotería: ").strip())

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        detalle_sql = """
            SELECT
                p.fecha_sorteo,
                p.codigo_extracto,
                e.provincia,
                e.nombre_extracto,
                q.n_apues,
                q.n_cupon,
                q.n_linea,
                p.numero_apostado,
                p.numero_resultado,
                p.orden_resultado,
                p.cifras_acertadas,
                p.importe_apostado,
                p.multiplicador,
                p.premio_total
            FROM premios p
            JOIN quiniela_exp q
                ON q.id = p.quiniela_exp_id
            JOIN extractos e
                ON e.codigo_extracto = p.codigo_extracto
            WHERE p.fecha_sorteo = %s
              AND p.codigo_extracto = %s
            ORDER BY q.n_apues, q.n_cupon, q.n_linea;
        """

        resumen_sql = """
            SELECT
                p.fecha_sorteo,
                p.codigo_extracto,
                e.provincia,
                e.nombre_extracto,
                COUNT(*) AS cantidad_ganadores,
                COALESCE(SUM(p.premio_total), 0) AS total_a_pagar
            FROM premios p
            JOIN extractos e
                ON e.codigo_extracto = p.codigo_extracto
            WHERE p.fecha_sorteo = %s
              AND p.codigo_extracto = %s
            GROUP BY
                p.fecha_sorteo,
                p.codigo_extracto,
                e.provincia,
                e.nombre_extracto;
        """

        df_detalle = pd.read_sql(detalle_sql, conn, params=(fecha, codigo_extracto))
        df_resumen = pd.read_sql(resumen_sql, conn, params=(fecha, codigo_extracto))

        if df_detalle.empty:
            print("\nNo hay premios calculados para esa lotería en esa fecha.")
            return

        nombre_extracto = df_detalle.iloc[0]["nombre_extracto"]

        carpeta_salida = Path("informes")
        carpeta_salida.mkdir(exist_ok=True)

        nombre_archivo = (
            f"informe_{fecha}_{codigo_extracto}_"
            f"{limpiar_nombre_archivo(nombre_extracto)}.xlsx"
        )
        ruta_salida = carpeta_salida / nombre_archivo

        with pd.ExcelWriter(ruta_salida, engine="openpyxl") as writer:
            df_resumen.to_excel(writer, sheet_name="Resumen", index=False)
            df_detalle.to_excel(writer, sheet_name="Ganadores", index=False)

            workbook = writer.book

            for hoja in ["Resumen", "Ganadores"]:
                ws = workbook[hoja]

                for column_cells in ws.columns:
                    max_length = 0
                    column_letter = column_cells[0].column_letter

                    for cell in column_cells:
                        valor = "" if cell.value is None else str(cell.value)
                        if len(valor) > max_length:
                            max_length = len(valor)

                    ws.column_dimensions[column_letter].width = max_length + 2

        print("\n✔ Informe generado correctamente.")
        print(f"Archivo: {ruta_salida}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()