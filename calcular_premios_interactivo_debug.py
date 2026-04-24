from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import psycopg2
from config import DB_CONFIG


FECHA = 20260312
EXTRACTO = 51

# filtros opcionales
SOLO_CUPON = None  # ej: 14975
MOSTRAR_SOLO_CON_DIFERENCIA = True
TOP_LINEAS = 200
TOP_CUPONES = 100


def limpiar_numero_apostado(numero: str) -> str:
    return str(numero).strip()


def normalizar_resultado(numero: str) -> str:
    return str(numero).strip().zfill(4)


def coincide_apuesta_con_resultado(numero_apostado: str, numero_resultado: str) -> int:
    apuesta = limpiar_numero_apostado(numero_apostado)
    resultado = normalizar_resultado(numero_resultado)

    if len(apuesta) == 4 and apuesta == resultado:
        return 4
    if len(apuesta) == 3 and apuesta == resultado[-3:]:
        return 3
    if len(apuesta) == 2 and apuesta == resultado[-2:]:
        return 2
    if len(apuesta) == 1 and apuesta == resultado[-1:]:
        return 1

    return 0


def clave_logica(numero_apostado: str, numero_resultado: str) -> str:
    """
    Clave del match lógico para comparar escenario alternativo.
    """
    apuesta = limpiar_numero_apostado(numero_apostado)
    resultado = normalizar_resultado(numero_resultado)

    if len(apuesta) == 4:
        return resultado
    if len(apuesta) == 3:
        return resultado[-3:]
    if len(apuesta) == 2:
        return resultado[-2:]
    if len(apuesta) == 1:
        return resultado[-1:]

    return resultado


def puesto_esta_en_rango(orden, desde, hasta):
    desde = 0 if desde is None else int(desde)
    hasta = 0 if hasta is None else int(hasta)

    if hasta <= 0:
        return False

    if desde == 0:
        return 1 <= orden <= hasta

    return desde <= orden <= hasta


def cantidad_puestos_jugados(desde, hasta):
    desde = 0 if desde is None else int(desde)
    hasta = 0 if hasta is None else int(hasta)

    if hasta <= 0:
        return 0

    if desde == 0:
        return hasta

    return hasta - desde + 1


def obtener_multiplicador(cifras, p4, p3, p2, p1):
    return {4: Decimal(str(p4)), 3: Decimal(str(p3)), 2: Decimal(str(p2)), 1: Decimal(str(p1))}.get(cifras, Decimal("0"))


def calcular_premio_unitario(importe, multiplicador, puestos):
    if puestos <= 0:
        return Decimal("0.00")

    val = (Decimal(str(importe)) * Decimal(str(multiplicador))) / Decimal(puestos)
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def formatear_importe(valor) -> str:
    valor = Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    texto = f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        print(f"=== COMPARADOR EXTRACTO {EXTRACTO} / FECHA {FECHA} ===\n")

        cur.execute("""
            SELECT
                premio_4_cifras,
                premio_3_cifras,
                premio_2_cifras,
                premio_1_cifra,
                provincia,
                nombre_extracto
            FROM extractos
            WHERE codigo_extracto = %s
        """, (EXTRACTO,))
        row = cur.fetchone()

        if not row:
            print("No existe ese extracto.")
            return

        p4, p3, p2, p1, provincia, nombre_extracto = row
        print(f"Lotería: {provincia} - {nombre_extracto}")
        print(f"Premios: 4c={p4}, 3c={p3}, 2c={p2}, 1c={p1}\n")

        cur.execute("""
            SELECT orden_resultado, numero_resultado
            FROM resultados
            WHERE fecha_sorteo = %s
              AND codigo_extracto = %s
            ORDER BY orden_resultado
        """, (FECHA, EXTRACTO))
        resultados = cur.fetchall()

        print("Resultados:")
        for orden, numero in resultados:
            print(f"  {orden:>2}: {normalizar_resultado(numero)}")

        sql = """
            SELECT
                id,
                n_agent,
                n_subag,
                n_maqui,
                n_cupon,
                n_linea,
                c_nroapos,
                n_impapos,
                n_alcdes,
                n_alchas
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND n_codext = %s
              AND COALESCE(c_ecupon, '') <> 'A'
        """
        params = [FECHA, EXTRACTO]

        if SOLO_CUPON is not None:
            sql += " AND n_cupon = %s"
            params.append(SOLO_CUPON)

        sql += " ORDER BY n_agent, n_subag, n_maqui, n_cupon, n_linea, id"

        cur.execute(sql, tuple(params))
        rows = cur.fetchall()

        if not rows:
            print("No hay apuestas para ese filtro.")
            return

        total_actual = Decimal("0.00")
        total_alternativo = Decimal("0.00")

        detalle_lineas = []
        total_por_cupon_actual = defaultdict(lambda: Decimal("0.00"))
        total_por_cupon_alt = defaultdict(lambda: Decimal("0.00"))

        for r in rows:
            (
                linea_id,
                n_agent,
                n_subag,
                n_maqui,
                n_cupon,
                n_linea,
                c_nroapos,
                n_impapos,
                n_alcdes,
                n_alchas,
            ) = r

            numero = limpiar_numero_apostado(c_nroapos)
            importe = Decimal(str(n_impapos))
            desde = 0 if n_alcdes is None else int(n_alcdes)
            hasta = 0 if n_alchas is None else int(n_alchas)

            if not numero:
                continue

            puestos = cantidad_puestos_jugados(desde, hasta)
            if puestos <= 0:
                continue

            hits = []

            for orden, res in resultados:
                if puesto_esta_en_rango(orden, desde, hasta):
                    cifras = coincide_apuesta_con_resultado(numero, res)
                    if cifras:
                        mult = obtener_multiplicador(cifras, p4, p3, p2, p1)
                        prem = calcular_premio_unitario(importe, mult, puestos)
                        clave = clave_logica(numero, res)

                        hits.append({
                            "orden": orden,
                            "resultado": normalizar_resultado(res),
                            "cifras": cifras,
                            "multiplicador": mult,
                            "premio": prem,
                            "clave": clave,
                        })

            if not hits:
                continue

            total_linea_actual = sum((h["premio"] for h in hits), Decimal("0.00"))

            agrupados = {}
            for h in hits:
                if h["clave"] not in agrupados:
                    agrupados[h["clave"]] = h

            hits_alt = list(agrupados.values())
            total_linea_alt = sum((h["premio"] for h in hits_alt), Decimal("0.00"))
            diferencia = total_linea_actual - total_linea_alt

            key_cupon = (n_agent, n_subag, n_maqui, n_cupon)
            total_por_cupon_actual[key_cupon] += total_linea_actual
            total_por_cupon_alt[key_cupon] += total_linea_alt

            detalle_lineas.append({
                "linea_id": linea_id,
                "n_agent": n_agent,
                "n_subag": n_subag,
                "n_maqui": n_maqui,
                "n_cupon": n_cupon,
                "n_linea": n_linea,
                "numero": numero,
                "importe": importe,
                "desde": desde,
                "hasta": hasta,
                "puestos": puestos,
                "hits": hits,
                "hits_alt": hits_alt,
                "total_actual": total_linea_actual,
                "total_alt": total_linea_alt,
                "diferencia": diferencia,
            })

            total_actual += total_linea_actual
            total_alternativo += total_linea_alt

        print("\n" + "=" * 120)
        print("RESUMEN GENERAL")
        print("=" * 120)
        print(f"TOTAL ACTUAL      : {formatear_importe(total_actual)}")
        print(f"TOTAL ALTERNATIVO : {formatear_importe(total_alternativo)}")
        print(f"DIFERENCIA        : {formatear_importe(total_actual - total_alternativo)}")

        lineas_con_dif = [x for x in detalle_lineas if x["diferencia"] > 0]
        print(f"LINEAS CON DIFERENCIA: {len(lineas_con_dif)}")

        cupones_con_dif = []
        for key in total_por_cupon_actual.keys():
            dif = total_por_cupon_actual[key] - total_por_cupon_alt[key]
            if dif > 0:
                cupones_con_dif.append((key, total_por_cupon_actual[key], total_por_cupon_alt[key], dif))

        print(f"CUPONES CON DIFERENCIA: {len(cupones_con_dif)}")

        print("\n" + "=" * 120)
        print(f"TOP {TOP_LINEAS} LINEAS POR DIFERENCIA")
        print("=" * 120)

        mostrar_lineas = sorted(lineas_con_dif, key=lambda x: x["diferencia"], reverse=True)
        if MOSTRAR_SOLO_CON_DIFERENCIA:
            mostrar_lineas = [x for x in mostrar_lineas if x["diferencia"] > 0]

        for item in mostrar_lineas[:TOP_LINEAS]:
            print("-" * 120)
            print(
                f"CUPON {item['n_agent']}-{item['n_subag']}-{item['n_maqui']}-{item['n_cupon']} | "
                f"LINEA {item['n_linea']} | ID {item['linea_id']} | "
                f"NUM {item['numero']!r} | IMP {formatear_importe(item['importe'])} | "
                f"RANGO {item['desde']}-{item['hasta']} | PUESTOS {item['puestos']}"
            )
            print(f"TOTAL ACTUAL: {formatear_importe(item['total_actual'])}")
            print(f"TOTAL ALT   : {formatear_importe(item['total_alt'])}")
            print(f"DIFERENCIA  : {formatear_importe(item['diferencia'])}")

            print("  HITS ACTUAL:")
            for h in item["hits"]:
                print(
                    f"    -> orden={h['orden']:>2} "
                    f"res={h['resultado']} "
                    f"cifras={h['cifras']} "
                    f"clave={h['clave']} "
                    f"premio={formatear_importe(h['premio'])}"
                )

            print("  HITS ALT:")
            for h in item["hits_alt"]:
                print(
                    f"    -> orden={h['orden']:>2} "
                    f"res={h['resultado']} "
                    f"cifras={h['cifras']} "
                    f"clave={h['clave']} "
                    f"premio={formatear_importe(h['premio'])}"
                )

        print("\n" + "=" * 120)
        print(f"TOP {TOP_CUPONES} CUPONES POR DIFERENCIA")
        print("=" * 120)

        cupones_con_dif = sorted(cupones_con_dif, key=lambda x: x[3], reverse=True)

        for key, actual, alt, dif in cupones_con_dif[:TOP_CUPONES]:
            ag, sub, maq, cup = key
            print(
                f"CUPON {ag}-{sub}-{maq}-{cup} | "
                f"ACTUAL={formatear_importe(actual)} | "
                f"ALT={formatear_importe(alt)} | "
                f"DIF={formatear_importe(dif)}"
            )

    except Exception as e:
        print("ERROR:", e)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()