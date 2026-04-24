from decimal import Decimal, ROUND_HALF_UP
import psycopg2
from config import DB_CONFIG


# ============================
# CONFIG DEBUG
# ============================

DEBUG_CUPONES = {32507, 9418, 32924, 41553, 69630, 14878}
DEBUG_ACTIVO = True


# ============================
# HELPERS BÁSICOS
# ============================

def limpiar_numero_apostado(numero: str) -> str:
    return str(numero).strip()


def normalizar_resultado(numero: str) -> str:
    return str(numero).strip().zfill(4)


def coincide_apuesta_con_resultado(numero_apostado: str, numero_resultado: str) -> int:
    """
    Compara exacto por sufijo según cantidad de cifras jugadas.
    """
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
    return {4: p4, 3: p3, 2: p2, 1: p1}.get(cifras, 0)


def calcular_premio_unitario(importe, multiplicador, puestos):
    if puestos <= 0:
        return Decimal("0.00")

    val = (Decimal(str(importe)) * Decimal(str(multiplicador))) / Decimal(puestos)
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def formatear_importe(valor: Decimal) -> str:
    valor = Decimal(valor).quantize(Decimal("0.01"))
    texto = f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


# ============================
# APROXIMADOS
# ============================

def numero_anterior(valor, ancho):
    n = int(valor)
    if n == 0:
        return None
    return str(n - 1).zfill(ancho)


def numero_siguiente(valor, ancho):
    n = int(valor)
    if n == (10**ancho - 1):
        return None
    return str(n + 1).zfill(ancho)


def es_a_la_cabeza(desde, hasta):
    desde = 0 if desde is None else int(desde)
    hasta = 0 if hasta is None else int(hasta)
    return desde == 0 and hasta == 1


def buscar_aproximado(numero_apostado, resultados, aprox4, aprox3):
    """
    Aproximado solo:
    - a la cabeza
    - contra el primer premio
    - para 4 y 3 cifras
    """
    if not resultados:
        return None

    orden, primer = resultados[0]
    primer = normalizar_resultado(primer)
    apuesta = limpiar_numero_apostado(numero_apostado)

    if len(apuesta) == 4:
        if apuesta in [numero_anterior(primer, 4), numero_siguiente(primer, 4)]:
            return ("aprox_4", orden, primer, 4, Decimal(str(aprox4)))

    if len(apuesta) == 3:
        cola = primer[-3:]
        if apuesta in [numero_anterior(cola, 3), numero_siguiente(cola, 3)]:
            return ("aprox_3", orden, primer, 3, Decimal(str(aprox3)))

    return None


# ============================
# REDOBLONA
# ============================

def ajustar_rango_detalle_redoblona(base_desde, base_hasta, det_desde, det_hasta):
    """
    Regla de negocio:
    - Si la base es exactamente 0,1 -> el detalle arranca en 2 y termina en hasta_detalle + 1
      Ej:
        detalle 0,5  -> 2..6
        detalle 0,10 -> 2..11
        detalle 0,20 -> 2..20
    - Si la base es mayor a 0,1 -> el detalle se mantiene igual
    """
    b_desde = 0 if base_desde is None else int(base_desde)
    b_hasta = 0 if base_hasta is None else int(base_hasta)
    d_desde = 0 if det_desde is None else int(det_desde)
    d_hasta = 0 if det_hasta is None else int(det_hasta)

    if b_desde == 0 and b_hasta == 1:
        nuevo_desde = 2
        nuevo_hasta = min(d_hasta + 1, 20)
        return nuevo_desde, nuevo_hasta

    return d_desde, d_hasta


def calcular_tope_redoblona(importe, desde, hasta, tope_redoblona):
    puestos = cantidad_puestos_jugados(desde, hasta)
    if puestos <= 0:
        return Decimal("0.00")

    return (
        Decimal(str(importe)) * Decimal(str(tope_redoblona)) / Decimal(puestos)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def obtener_hits(numero, desde, hasta, resultados):
    """
    Devuelve todas las coincidencias válidas dentro del rango.
    Cada hit = (orden, resultado, cifras)
    """
    hits = []
    for orden, res in resultados:
        if puesto_esta_en_rango(orden, desde, hasta):
            cifras = coincide_apuesta_con_resultado(numero, res)
            if cifras:
                hits.append((orden, res, cifras))
    return hits


# ============================
# INSERT
# ============================

def insertar(cur, data):
    cur.execute("""
        INSERT INTO premios (
            quiniela_exp_id,
            fecha_sorteo,
            codigo_extracto,
            numero_apostado,
            numero_resultado,
            orden_resultado,
            cifras_acertadas,
            importe_apostado,
            multiplicador,
            premio_total,
            tipo_jugada
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """, data)


# ============================
# MAIN
# ============================

def main():
    fecha = int(input("Fecha: ").strip())
    cod = int(input("Extracto: ").strip())

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                premio_4_cifras,
                premio_3_cifras,
                premio_2_cifras,
                premio_1_cifra,
                aprox_4_cifras,
                aprox_3_cifras,
                tope_redoblona,
                provincia,
                nombre_extracto
            FROM extractos
            WHERE codigo_extracto = %s
        """, (cod,))
        row = cur.fetchone()

        if not row:
            print("No existe ese extracto.")
            return

        p4, p3, p2, p1, aprox4, aprox3, tope_red, provincia, nombre_extracto = row

        aprox4 = Decimal(str(aprox4 if aprox4 is not None else 100))
        aprox3 = Decimal(str(aprox3 if aprox3 is not None else 10))
        tope_red = Decimal(str(tope_red if tope_red is not None else 1000))

        cur.execute("""
            DELETE FROM premios
            WHERE fecha_sorteo = %s
              AND codigo_extracto = %s
        """, (fecha, cod))

        cur.execute("""
            SELECT orden_resultado, numero_resultado
            FROM resultados
            WHERE fecha_sorteo = %s
              AND codigo_extracto = %s
            ORDER BY orden_resultado
        """, (fecha, cod))
        resultados = cur.fetchall()

        if not resultados:
            print("No hay resultados cargados para esa lotería en esa fecha.")
            return

        cur.execute("""
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
                n_alchas,
                c_ecupon,
                es_redoblona_base,
                es_redoblona_detalle,
                redoblona_grupo
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND n_codext = %s
              AND COALESCE(c_ecupon, '') <> 'A'
            ORDER BY id
        """, (fecha, cod))
        rows = cur.fetchall()

        if not rows:
            print("No hay apuestas para esa lotería en esa fecha.")
            return

        grupos = {}
        apuestas = []

        for r in rows:
            reg = {
                "id": r[0],
                "n_agent": r[1],
                "n_subag": r[2],
                "n_maqui": r[3],
                "n_cupon": r[4],
                "n_linea": r[5],
                "c_nroapos": limpiar_numero_apostado(r[6]),
                "n_impapos": Decimal(str(r[7])).quantize(Decimal("0.01")),
                "n_alcdes": 0 if r[8] is None else int(r[8]),
                "n_alchas": 0 if r[9] is None else int(r[9]),
                "c_ecupon": r[10],
                "es_redoblona_base": bool(r[11]),
                "es_redoblona_detalle": bool(r[12]),
                "redoblona_grupo": r[13],
            }

            apuestas.append(reg)

            if reg["redoblona_grupo"] is not None:
                grupos.setdefault(reg["redoblona_grupo"], []).append(reg)

        total = Decimal("0.00")

        for actual in apuestas:
            numero = actual["c_nroapos"]
            importe = actual["n_impapos"]
            desde = actual["n_alcdes"]
            hasta = actual["n_alchas"]

            if not numero:
                continue

            puestos = cantidad_puestos_jugados(desde, hasta)
            if puestos <= 0:
                continue

            if actual["es_redoblona_detalle"]:
                continue

            # ============================
            # REDOBLONA
            # ============================
            if actual["es_redoblona_base"]:
                grupo = actual["redoblona_grupo"]
                detalle = next(
                    (x for x in grupos.get(grupo, []) if x["es_redoblona_detalle"]),
                    None
                )

                if not detalle:
                    continue

                hits_base = obtener_hits(numero, desde, hasta, resultados)
                if not hits_base:
                    continue

                orden_base, res_base, cifras_base = hits_base[0]
                mult_base = obtener_multiplicador(cifras_base, p4, p3, p2, p1)
                if mult_base <= 0:
                    continue

                if es_a_la_cabeza(desde, hasta):
                    rep_base = 1
                else:
                    rep_base = len(hits_base)

                premio_base_unitario = calcular_premio_unitario(
                    importe,
                    mult_base,
                    cantidad_puestos_jugados(desde, hasta)
                )

                premio_base_total = (
                    premio_base_unitario * Decimal(rep_base)
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                tope = calcular_tope_redoblona(importe, desde, hasta, tope_red)

                d2, h2 = ajustar_rango_detalle_redoblona(
                    desde,
                    hasta,
                    detalle["n_alcdes"],
                    detalle["n_alchas"]
                )

                hits_detalle = obtener_hits(detalle["c_nroapos"], d2, h2, resultados)
                if not hits_detalle:
                    continue

                orden_det, res_det, cifras_det = hits_detalle[0]
                mult_det = obtener_multiplicador(cifras_det, p4, p3, p2, p1)
                if mult_det <= 0:
                    continue

                rep_detalle = len(hits_detalle)

                premio_detalle_unitario = calcular_premio_unitario(
                    premio_base_total,
                    mult_det,
                    cantidad_puestos_jugados(d2, h2)
                )

                premio_detalle_total = (
                    premio_detalle_unitario * Decimal(rep_detalle)
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                premio_final = min(premio_detalle_total, tope).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                if DEBUG_ACTIVO and actual["n_cupon"] in DEBUG_CUPONES:
                    print(
                        f"[RED] agencia={actual['n_agent']} sub={actual['n_subag']} maq={actual['n_maqui']} "
                        f"cupon={actual['n_cupon']} linea={actual['n_linea']} "
                        f"base={numero} {desde}-{hasta} rep_base={rep_base} "
                        f"detalle={detalle['c_nroapos']} {detalle['n_alcdes']}-{detalle['n_alchas']} "
                        f"ajustado={d2}-{h2} rep_det={rep_detalle} "
                        f"premio_base_unit={premio_base_unitario} premio_base_total={premio_base_total} "
                        f"premio_det_unit={premio_detalle_unitario} premio_det_total={premio_detalle_total} "
                        f"tope={tope} premio_final={premio_final}"
                    )

                if premio_final > Decimal("0.00"):
                    total += premio_final

                    insertar(cur, (
                        actual["id"],
                        fecha,
                        cod,
                        f"{numero}/{detalle['c_nroapos']}",
                        normalizar_resultado(res_det),
                        orden_det,
                        cifras_det,
                        importe,
                        mult_det,
                        premio_final,
                        "redoblona"
                    ))

                continue

            # ============================
            # NORMALES
            # ============================
            for orden, res in resultados:
                if puesto_esta_en_rango(orden, desde, hasta):
                    cifras = coincide_apuesta_con_resultado(numero, res)
                    if cifras:
                        mult = obtener_multiplicador(cifras, p4, p3, p2, p1)
                        if mult > 0:
                            premio = calcular_premio_unitario(
                                importe,
                                mult,
                                cantidad_puestos_jugados(desde, hasta)
                            )

                            total += premio

                            insertar(cur, (
                                actual["id"],
                                fecha,
                                cod,
                                numero,
                                normalizar_resultado(res),
                                orden,
                                cifras,
                                importe,
                                mult,
                                premio,
                                "normal"
                            ))

            # ============================
            # APROXIMADOS
            # ============================
            if es_a_la_cabeza(desde, hasta):
                aprox = buscar_aproximado(numero, resultados, aprox4, aprox3)

                if aprox:
                    tipo, orden, res, cifras, mult = aprox
                    premio = (importe * Decimal(mult)).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )

                    total += premio

                    insertar(cur, (
                        actual["id"],
                        fecha,
                        cod,
                        numero,
                        normalizar_resultado(res),
                        orden,
                        cifras,
                        importe,
                        mult,
                        premio,
                        tipo
                    ))

        conn.commit()

        # ============================
        # RESUMEN
        # ============================

        cur.execute("""
            SELECT COALESCE(SUM(premio_total), 0)
            FROM premios
            WHERE fecha_sorteo = %s
              AND codigo_extracto = %s
              AND tipo_jugada = 'normal'
        """, (fecha, cod))
        total_normales = Decimal(str(cur.fetchone()[0] or 0)).quantize(Decimal("0.01"))

        cur.execute("""
            SELECT COALESCE(SUM(premio_total), 0)
            FROM premios
            WHERE fecha_sorteo = %s
              AND codigo_extracto = %s
              AND tipo_jugada IN ('aprox_3', 'aprox_4')
        """, (fecha, cod))
        total_aprox = Decimal(str(cur.fetchone()[0] or 0)).quantize(Decimal("0.01"))

        cur.execute("""
            SELECT COALESCE(SUM(premio_total), 0)
            FROM premios
            WHERE fecha_sorteo = %s
              AND codigo_extracto = %s
              AND tipo_jugada = 'redoblona'
        """, (fecha, cod))
        total_red = Decimal(str(cur.fetchone()[0] or 0)).quantize(Decimal("0.01"))

        # PREMIO = linea premiada (no hit)
        cur.execute("""
            SELECT COUNT(DISTINCT quiniela_exp_id)
            FROM premios
            WHERE fecha_sorteo = %s
              AND codigo_extracto = %s
        """, (fecha, cod))
        cant_premios = cur.fetchone()[0] or 0

        # CUPON premiado = cupón con suma positiva
        cur.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT
                    q.n_agent,
                    q.n_subag,
                    q.n_maqui,
                    q.n_cupon,
                    SUM(p.premio_total) AS total_cupon
                FROM premios p
                JOIN quiniela_exp q ON q.id = p.quiniela_exp_id
                WHERE p.fecha_sorteo = %s
                  AND p.codigo_extracto = %s
                GROUP BY
                    q.n_agent,
                    q.n_subag,
                    q.n_maqui,
                    q.n_cupon
                HAVING SUM(p.premio_total) > 0
            ) t
        """, (fecha, cod))
        cant_cupones = cur.fetchone()[0] or 0

        print("\n=== RESULTADO ===")
        print(f"Lotería: {provincia} - {nombre_extracto}")
        print(f"TOTAL: {formatear_importe(total)}")
        print(f"NORMALES: {formatear_importe(total_normales)}")
        print(f"APROX: {formatear_importe(total_aprox)}")
        print(f"RED: {formatear_importe(total_red)}")
        print(f"PREMIOS: {cant_premios}")
        print(f"CUPONES: {cant_cupones}")

        if DEBUG_ACTIVO:
            cur.execute("""
                SELECT tipo_jugada, COUNT(*), COALESCE(SUM(premio_total), 0)
                FROM premios
                WHERE fecha_sorteo = %s
                  AND codigo_extracto = %s
                GROUP BY tipo_jugada
                ORDER BY tipo_jugada
            """, (fecha, cod))
            print("\nDEBUG PREMIOS:")
            for row in cur.fetchall():
                print(row)

    except Exception as e:
        conn.rollback()
        print("Error:", e)

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()