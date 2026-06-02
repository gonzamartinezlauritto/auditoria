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
                  AND codigo_extracto = %s
            """, (fecha, codigo_extracto))

            for orden, numero in enumerate(numeros, start=1):
                cur.execute("""
                    INSERT INTO resultados (
                        fecha_sorteo,
                        codigo_extracto,
                        orden_resultado,
                        numero_resultado
                    )
                    VALUES (%s, %s, %s, %s)
                """, (
                    fecha,
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