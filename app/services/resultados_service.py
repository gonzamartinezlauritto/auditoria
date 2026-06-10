from app.database import get_connection


def normalizar_numero(numero: str) -> str:
    return str(numero).strip().zfill(4)


def cargar_resultados(fecha: int, turno: str, resultados: list):
    turno = turno.upper()
    conn = get_connection()
    cur = conn.cursor()

    try:
        total_insertados = 0

        for item in resultados:
            codigo_extracto = int(item["codigo_extracto"])
            numeros = [normalizar_numero(n) for n in item["numeros"]]

            if len(numeros) != 20:
                raise Exception(
                    f"El extracto {codigo_extracto} tiene {len(numeros)} números. Deben ser 20."
                )

            cur.execute("""
                DELETE FROM resultados
                WHERE fecha_sorteo = %s
                AND turno = %s
                AND codigo_extracto = %s
            """, (fecha, turno, codigo_extracto))

            for orden, numero in enumerate(numeros, start=1):
                cur.execute("""
                    INSERT INTO resultados (
                        fecha_sorteo,
                        turno,
                        codigo_extracto,
                        orden_resultado,
                        numero_resultado
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    fecha,
                    turno,
                    codigo_extracto,
                    orden,
                    numero,
                ))

                total_insertados += 1

        conn.commit()

        return {
            "ok": True,
            "fecha": fecha,
            "turno": turno,
            "extractos_cargados": len(resultados),
            "resultados_insertados": total_insertados,
        }

    except Exception as e:
        conn.rollback()
        return {
            "ok": False,
            "error": str(e),
        }

    finally:
        cur.close()
        conn.close()

def obtener_resultados_por_fecha(fecha: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                r.turno,
                r.codigo_extracto,
                e.nombre_extracto,
                r.orden_resultado,
                r.numero_resultado
            FROM resultados r
            JOIN extractos e
                ON e.codigo_extracto = r.codigo_extracto
            WHERE r.fecha_sorteo = %s
            ORDER BY
                r.turno,
                r.codigo_extracto,
                r.orden_resultado
        """, (fecha,))

        rows = cur.fetchall()

        data = {}

        for turno, codigo, nombre, orden, numero in rows:
            if turno not in data:
                data[turno] = {}

            if codigo not in data[turno]:
                data[turno][codigo] = {
                    "codigo_extracto": codigo,
                    "nombre_extracto": nombre,
                    "numeros": []
                }

            data[turno][codigo]["numeros"].append({
                "orden": orden,
                "numero": numero
            })

        return {
            "ok": True,
            "fecha": fecha,
            "resultados": data
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

    finally:
        cur.close()
        conn.close()