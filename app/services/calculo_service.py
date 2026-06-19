from decimal import Decimal, ROUND_HALF_UP

from app.database import get_connection

def obtener_extractos_del_turno(cur, fecha: int, turno: str):
    cur.execute("""
        SELECT DISTINCT n_codext
        FROM quiniela_exp
        WHERE n_fsorteo = %s
          AND TRIM(c_tsorteo) = %s
          AND COALESCE(c_ecupon, '') = 'N'
          AND COALESCE(n_nodef, 0) <> 1
        ORDER BY n_codext
    """, (fecha, turno.upper()))

    return [row[0] for row in cur.fetchall()]


def redondear_a_diez_centavos(valor):
    valor = Decimal(str(valor or 0))
    return (
        (valor / Decimal("0.10"))
        .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        * Decimal("0.10")
    ).quantize(Decimal("0.01"))


def limpiar_numero(numero):
    return str(numero or "").strip()


def normalizar_resultado(numero):
    return str(numero or "").strip().zfill(4)


def coincide(numero_apostado, numero_resultado):
    apuesta = limpiar_numero(numero_apostado)
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


def puesto_en_rango(orden, desde, hasta):
    desde = int(desde or 0)
    hasta = int(hasta or 0)

    if hasta <= 0:
        return False

    if desde == 0:
        return 1 <= orden <= hasta

    return desde <= orden <= hasta


def cantidad_puestos(desde, hasta):
    desde = int(desde or 0)
    hasta = int(hasta or 0)

    if hasta <= 0:
        return 0

    if desde == 0:
        return hasta

    return hasta - desde + 1


def obtener_multiplicador(cifras, p4, p3, p2, p1):
    return {
        4: Decimal(str(p4)),
        3: Decimal(str(p3)),
        2: Decimal(str(p2)),
        1: Decimal(str(p1)),
    }.get(cifras, Decimal("0"))


def calcular_premio(importe, multiplicador, puestos):
    if puestos <= 0:
        return Decimal("0.00")

    return (
        Decimal(str(importe)) * Decimal(str(multiplicador)) / Decimal(puestos)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def formatear(valor):
    valor = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def insertar_premio(cur, data):
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
            tipo_jugada,
            quiniela_exp_id_redoblona,
            premio_base_redoblona
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, data)


def obtener_hits(numero, desde, hasta, resultados):
    hits = []

    for orden, res in resultados:
        if not puesto_en_rango(orden, desde, hasta):
            continue

        cifras = coincide(numero, res)

        if cifras:
            hits.append((orden, res, cifras))

    return hits


def es_a_la_cabeza(desde, hasta):
    return int(desde or 0) == 0 and int(hasta or 0) == 1


def numero_anterior(valor, ancho):
    n = int(valor)
    if n == 0:
        return None
    return str(n - 1).zfill(ancho)


def numero_siguiente(valor, ancho):
    n = int(valor)
    if n == (10 ** ancho) - 1:
        return None
    return str(n + 1).zfill(ancho)


def buscar_aproximado(numero, resultados, aprox4, aprox3):
    if not resultados:
        return None

    orden, primero = resultados[0]
    primero = normalizar_resultado(primero)
    apuesta = limpiar_numero(numero)

    if len(apuesta) == 4:
        if apuesta in (numero_anterior(primero, 4), numero_siguiente(primero, 4)):
            return "aprox_4", orden, primero, 4, Decimal(str(aprox4))

    if len(apuesta) == 3:
        cola = primero[-3:]
        if apuesta in (numero_anterior(cola, 3), numero_siguiente(cola, 3)):
            return "aprox_3", orden, primero, 3, Decimal(str(aprox3))

    return None


def ajustar_rango_detalle_redoblona(base_desde, base_hasta, det_desde, det_hasta):
    base_desde = int(base_desde or 0)
    base_hasta = int(base_hasta or 0)
    det_desde = int(det_desde or 0)
    det_hasta = int(det_hasta or 0)

    if base_desde == 0 and base_hasta == 1:
        return 2, min(det_hasta + 1, 20)

    return det_desde, det_hasta


def calcular_tope_redoblona(importe, desde, hasta, tope_redoblona):
    puestos = cantidad_puestos(desde, hasta)
    if puestos <= 0:
        return Decimal("0.00")

    return (
        Decimal(str(importe)) * Decimal(str(tope_redoblona)) / Decimal(puestos)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def marcar_redoblonas_por_patron(apuestas):
    apuestas = sorted(
        apuestas,
        key=lambda x: (
            x["n_agent"],
            x["n_subag"],
            x["n_maqui"],
            x["n_cupon"],
            x["n_codext"],
            x["n_linea"],
            x["id"],
        )
    )

    grupo = 1
    i = 0

    while i < len(apuestas) - 1:
        actual = apuestas[i]
        siguiente = apuestas[i + 1]

        misma_apuesta = (
            actual["n_agent"] == siguiente["n_agent"]
            and actual["n_subag"] == siguiente["n_subag"]
            and actual["n_maqui"] == siguiente["n_maqui"]
            and actual["n_cupon"] == siguiente["n_cupon"]
            and actual["n_codext"] == siguiente["n_codext"]
        )

        lineas_consecutivas = int(siguiente["n_linea"]) == int(actual["n_linea"]) + 1

        misma_cantidad_cifras = (
            len(actual["c_nroapos"]) > 0
            and len(actual["c_nroapos"]) == len(siguiente["c_nroapos"])
        )

        es_patron_redoblona = (
            misma_apuesta
            and lineas_consecutivas
            and misma_cantidad_cifras
            and actual["n_impapos"] > Decimal("0.00")
            and siguiente["n_impapos"] == Decimal("0.00")
        )

        if es_patron_redoblona:
            actual["es_redoblona_base"] = True
            actual["es_redoblona_detalle"] = False
            actual["redoblona_grupo"] = grupo

            siguiente["es_redoblona_base"] = False
            siguiente["es_redoblona_detalle"] = True
            siguiente["redoblona_grupo"] = grupo

            grupo += 1
            i += 2
        else:
            i += 1

    return apuestas


def obtener_cupones_ganadores_unicos(cur, fecha, turno):
    cur.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT
                q.n_agent,
                q.n_subag,
                q.n_maqui,
                q.n_cupon
            FROM premios p
            JOIN quiniela_exp q
                ON q.id = p.quiniela_exp_id
            WHERE p.fecha_sorteo = %s
              AND TRIM(q.c_tsorteo) = %s
              AND p.premio_total <> 0
            GROUP BY
                q.n_agent,
                q.n_subag,
                q.n_maqui,
                q.n_cupon
        ) t
    """, (fecha, turno))

    return cur.fetchone()[0] or 0


def obtener_cupones_ganadores_unicos_dbf(cur, fecha, turno):
    cur.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT
                agencia,
                subagencia,
                nromaquina,
                numero
            FROM aciertos_dbf
            WHERE fecha_sorteo = %s
              AND turno = %s
            GROUP BY
                agencia,
                subagencia,
                nromaquina,
                numero
        ) t
    """, (fecha, turno))

    return cur.fetchone()[0] or 0


def calcular_extracto(conn, fecha, turno, cod):
    turno = turno.upper()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            codigo_extracto,
            provincia,
            nombre_extracto,
            premio_4_cifras,
            premio_3_cifras,
            premio_2_cifras,
            premio_1_cifra,
            aprox_4_cifras,
            aprox_3_cifras,
            tope_redoblona
        FROM extractos
        WHERE codigo_extracto = %s
    """, (cod,))

    ext = cur.fetchone()

    if not ext:
        raise Exception(f"No existe extracto {cod}")

    (
        codigo_extracto,
        provincia,
        nombre_extracto,
        p4,
        p3,
        p2,
        p1,
        aprox4,
        aprox3,
        tope_redoblona,
    ) = ext

    aprox4 = Decimal(str(aprox4 or 100))
    aprox3 = Decimal(str(aprox3 or 10))
    tope_redoblona = Decimal(str(tope_redoblona or 1000))

    cur.execute("""
        DELETE FROM premios
        WHERE fecha_sorteo = %s
          AND codigo_extracto = %s
          AND quiniela_exp_id IN (
              SELECT id
              FROM quiniela_exp
              WHERE n_fsorteo = %s
                AND c_tsorteo = %s
                AND n_codext = %s
          )
    """, (fecha, cod, fecha, turno, cod))

    cur.execute("""
       SELECT orden_resultado, numero_resultado
        FROM resultados
        WHERE fecha_sorteo = %s
        AND turno = %s
        AND codigo_extracto = %s
        ORDER BY orden_resultado
    """, (fecha, turno, cod))

    resultados = cur.fetchall()

    if not resultados:
        raise Exception(f"No hay resultados cargados para fecha {fecha}, extracto {cod}")

    cur.execute("""
        SELECT
            id,
            n_apues,
            n_maqre,
            n_agent,
            n_subag,
            n_maqui,
            n_cupon,
            n_linea,
            n_femis,
            c_hemis,
            c_ecupon,
            n_fsorteo,
            n_codlot,
            c_tsorteo,
            n_alcdes,
            n_alchas,
            c_nroapos,
            n_impapos,
            n_nodef,
            n_codext,
            COALESCE(es_redoblona_base, false),
            COALESCE(es_redoblona_detalle, false),
            linea_base_id,
            redoblona_grupo
        FROM quiniela_exp
        WHERE n_fsorteo = %s
          AND c_tsorteo = %s
          AND n_codext = %s
          AND COALESCE(c_ecupon, '') = 'N'
          AND COALESCE(n_nodef, 0) <> 1
        ORDER BY n_agent, n_subag, n_maqui, n_cupon, n_linea, id
    """, (fecha, turno, cod))

    rows = cur.fetchall()

    apuestas = []

    for r in rows:
        apuestas.append({
            "id": r[0],
            "n_apues": r[1],
            "n_maqre": r[2],
            "n_agent": r[3],
            "n_subag": r[4],
            "n_maqui": r[5],
            "n_cupon": r[6],
            "n_linea": r[7],
            "n_femis": r[8],
            "c_hemis": r[9],
            "c_ecupon": r[10],
            "n_fsorteo": r[11],
            "n_codlot": r[12],
            "c_tsorteo": r[13],
            "n_alcdes": int(r[14] or 0),
            "n_alchas": int(r[15] or 0),
            "c_nroapos": limpiar_numero(r[16]),
            "n_impapos": Decimal(str(r[17] or 0)).quantize(Decimal("0.01")),
            "n_nodef": int(r[18] or 0),
            "n_codext": r[19],
            "es_redoblona_base": bool(r[20]),
            "es_redoblona_detalle": bool(r[21]),
            "linea_base_id": r[22],
            "redoblona_grupo": r[23],
        })

    apuestas = marcar_redoblonas_por_patron(apuestas)

    redoblonas_por_grupo = {}
    for a in apuestas:
        if a["redoblona_grupo"] is not None:
            redoblonas_por_grupo.setdefault(a["redoblona_grupo"], []).append(a)

    for actual in apuestas:
        numero = actual["c_nroapos"]
        importe = actual["n_impapos"]
        desde = actual["n_alcdes"]
        hasta = actual["n_alchas"]

        if not numero:
            continue

        if actual["es_redoblona_detalle"]:
            continue

        if actual["es_redoblona_base"]:
            grupo = actual["redoblona_grupo"]
            detalle = next(
                (x for x in redoblonas_por_grupo.get(grupo, []) if x["es_redoblona_detalle"]),
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

            puestos_base = cantidad_puestos(desde, hasta)

            premio_base_unit = calcular_premio(importe, mult_base, puestos_base)

            rep_base = len(hits_base)

            premio_base_total = (
                premio_base_unit * Decimal(rep_base)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            d_det, h_det = ajustar_rango_detalle_redoblona(
                desde,
                hasta,
                detalle["n_alcdes"],
                detalle["n_alchas"]
            )

            hits_detalle = obtener_hits(
                detalle["c_nroapos"],
                d_det,
                h_det,
                resultados
            )

            hits_detalle = [
                h for h in hits_detalle
                if h[0] != orden_base
            ]

            if not hits_detalle:
                continue

            orden_det, res_det, cifras_det = hits_detalle[0]
            mult_det = obtener_multiplicador(cifras_det, p4, p3, p2, p1)

            if mult_det <= 0:
                continue

            puestos_det = cantidad_puestos(d_det, h_det)

            premio_det_unit = calcular_premio(
                premio_base_total,
                mult_det,
                puestos_det
            )

            rep_det = len(hits_detalle)

            premio_det_total = (
                premio_det_unit * Decimal(rep_det)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            tope = calcular_tope_redoblona(
                importe,
                desde,
                hasta,
                tope_redoblona
            )

            premio_final = min(premio_det_total, tope).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            if premio_final <= 0:
                continue

            insertar_premio(cur, (
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
                "redoblona",
                detalle["id"],
                premio_base_total,
            ))

            continue

        if importe <= 0:
            continue

        hits = obtener_hits(numero, desde, hasta, resultados)

        for orden, res, cifras in hits:
            mult = obtener_multiplicador(cifras, p4, p3, p2, p1)

            if mult <= 0:
                continue

            puestos = cantidad_puestos(desde, hasta)
            premio = calcular_premio(importe, mult, puestos)

            if premio <= 0:
                continue

            insertar_premio(cur, (
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
                "normal",
                None,
                None,
            ))

        if es_a_la_cabeza(desde, hasta):
            aprox = buscar_aproximado(numero, resultados, aprox4, aprox3)

            if aprox:
                tipo, orden, res, cifras, mult = aprox
                premio = (importe * mult).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                if premio > 0:
                    insertar_premio(cur, (
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
                        tipo,
                        None,
                        None,
                    ))

    cur.execute("""
        SELECT COALESCE(SUM(p.premio_total), 0)
        FROM premios p
        JOIN quiniela_exp q ON q.id = p.quiniela_exp_id
        WHERE p.fecha_sorteo = %s
          AND p.codigo_extracto = %s
          AND q.c_tsorteo = %s
          AND p.tipo_jugada = 'normal'
    """, (fecha, cod, turno))
    total_normales = redondear_a_diez_centavos(
        Decimal(str(cur.fetchone()[0] or 0)) / Decimal("100")
    )

    cur.execute("""
        SELECT COALESCE(SUM(p.premio_total), 0)
        FROM premios p
        JOIN quiniela_exp q ON q.id = p.quiniela_exp_id
        WHERE p.fecha_sorteo = %s
          AND p.codigo_extracto = %s
          AND q.c_tsorteo = %s
          AND p.tipo_jugada IN ('aprox_3', 'aprox_4')
    """, (fecha, cod, turno))
    total_aprox = redondear_a_diez_centavos(
        Decimal(str(cur.fetchone()[0] or 0)) / Decimal("100")
    )

    cur.execute("""
        SELECT COALESCE(SUM(p.premio_total), 0)
        FROM premios p
        JOIN quiniela_exp q ON q.id = p.quiniela_exp_id
        WHERE p.fecha_sorteo = %s
          AND p.codigo_extracto = %s
          AND q.c_tsorteo = %s
          AND p.tipo_jugada = 'redoblona'
    """, (fecha, cod, turno))
    total_red = redondear_a_diez_centavos(
        Decimal(str(cur.fetchone()[0] or 0)) / Decimal("100")
    )

    total_final = redondear_a_diez_centavos(
        total_normales + total_aprox + total_red
    ).quantize(Decimal("0.01"))

    cur.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT DISTINCT
            q.n_agent,
            q.n_subag,
            q.n_maqui,
            q.n_cupon
        FROM premios p
        JOIN quiniela_exp q
            ON q.id = p.quiniela_exp_id
        WHERE p.fecha_sorteo = %s
          AND p.codigo_extracto = %s
          AND TRIM(q.c_tsorteo) = %s
          AND p.premio_total > 0
    ) t
    """, (fecha, cod, turno))

    cant_premios = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT COALESCE(SUM(n_impapos), 0)
        FROM quiniela_exp
        WHERE n_fsorteo = %s
          AND c_tsorteo = %s
          AND n_codext = %s
          AND COALESCE(c_ecupon, '') = 'N'
          AND COALESCE(n_nodef, 0) <> 1
          AND n_impapos > 0
    """, (fecha, turno, cod))
    total_recaudado = redondear_a_diez_centavos(
        Decimal(str(cur.fetchone()[0] or 0)) / Decimal("100")
    ).quantize(Decimal("0.01"))

    cur.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT
                n_agent,
                n_subag,
                n_maqui,
                n_cupon
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND c_tsorteo = %s
              AND n_codext = %s
              AND COALESCE(c_ecupon, '') = 'N'
              AND COALESCE(n_nodef, 0) <> 1
            GROUP BY n_agent, n_subag, n_maqui, n_cupon
        ) t
    """, (fecha, turno, cod))
    cupones_jugados = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT COUNT(*)
        FROM aciertos_dbf
        WHERE fecha_sorteo = %s
          AND turno = %s
          AND codigo_extracto = %s
    """, (fecha, turno, cod))
    archivo_aciertos_dbf = cur.fetchone()[0] or 0

    cur.close()

    return {
        "codigo_extracto": cod,
        "sorteo": nombre_extracto,
        "cupones_jugados": cupones_jugados,
        "recaudacion": total_recaudado,
        "importe_premiados": total_final,
        "apuestas_premiadas": cant_premios,
        "archivo_aciertos_dbf": archivo_aciertos_dbf,
    }


def guardar_resumen_auditoria(
    conn,
    fecha,
    turno,
    reportes,
    cupones_ganadores_unicos,
    cupones_ganadores_dbf
):
    cur = conn.cursor()

    for r in reportes:
        recaudacion = Decimal(str(r["recaudacion"]))
        importe_premiados = Decimal(str(r["importe_premiados"]))

        comision = (recaudacion * Decimal("0.20")).quantize(Decimal("0.01"))
        utilidad = (recaudacion - importe_premiados - comision).quantize(Decimal("0.01"))

        porcentaje_utilidad = Decimal("0.00")
        if recaudacion > 0:
            porcentaje_utilidad = (
                (utilidad / recaudacion) * Decimal("100")
            ).quantize(Decimal("0.01"))

        cur.execute("""
            INSERT INTO resumen_auditoria (
                fecha_sorteo,
                turno,
                codigo_extracto,
                sorteo,
                cupones_jugados,
                recaudacion,
                importe_premiados,
                comision,
                utilidad,
                porcentaje_utilidad,
                apuestas_premiadas,
                archivo_aciertos_dbf,
                cupones_ganadores_unicos,
                cupones_ganadores_dbf,
                fecha_calculo
            )
            VALUES (
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,NOW()
            )
            ON CONFLICT (fecha_sorteo, turno, codigo_extracto)
            DO UPDATE SET
                sorteo = EXCLUDED.sorteo,
                cupones_jugados = EXCLUDED.cupones_jugados,
                recaudacion = EXCLUDED.recaudacion,
                importe_premiados = EXCLUDED.importe_premiados,
                comision = EXCLUDED.comision,
                utilidad = EXCLUDED.utilidad,
                porcentaje_utilidad = EXCLUDED.porcentaje_utilidad,
                apuestas_premiadas = EXCLUDED.apuestas_premiadas,
                archivo_aciertos_dbf = EXCLUDED.archivo_aciertos_dbf,
                cupones_ganadores_unicos = EXCLUDED.cupones_ganadores_unicos,
                cupones_ganadores_dbf = EXCLUDED.cupones_ganadores_dbf,
                fecha_calculo = NOW()
        """, (
            fecha,
            turno,
            r["codigo_extracto"],
            r["sorteo"],
            r.get("cupones_jugados", 0),
            recaudacion,
            importe_premiados,
            comision,
            utilidad,
            porcentaje_utilidad,
            r.get("apuestas_premiadas", 0),
            r.get("archivo_aciertos_dbf", 0),
            cupones_ganadores_unicos,
            cupones_ganadores_dbf,
        ))

    cur.close()

def calcular_por_fecha_turno(fecha: int, turno: str):
    turno = turno.upper()
    conn = get_connection()

    try:

        reportes = []

        cur = conn.cursor()
        extractos = obtener_extractos_del_turno(cur, fecha, turno)
        cur.close()

        if not extractos:
            raise Exception(f"No hay extractos para fecha={fecha}, turno={turno}")

        for codigo_extracto in extractos:
            resultado = calcular_extracto(
                conn=conn,
                fecha=fecha,
                turno=turno,
                cod=codigo_extracto,
            )
            reportes.append(resultado)

        cur = conn.cursor()

        cupones_ganadores_unicos = obtener_cupones_ganadores_unicos(
            cur,
            fecha,
            turno,
        )

        cupones_ganadores_dbf = obtener_cupones_ganadores_unicos_dbf(
            cur,
            fecha,
            turno,
        )

        cur.close()

        guardar_resumen_auditoria(
            conn=conn,
            fecha=fecha,
            turno=turno,
            reportes=reportes,
            cupones_ganadores_unicos=cupones_ganadores_unicos,
            cupones_ganadores_dbf=cupones_ganadores_dbf,
        )

        conn.commit()

        return {
            "ok": True,
            "fecha": fecha,
            "turno": turno,
            "reportes": reportes,
            "cupones_ganadores_unicos": cupones_ganadores_unicos,
            "cupones_ganadores_dbf": cupones_ganadores_dbf,
        }

    except Exception as e:
        conn.rollback()
        return {
            "ok": False,
            "error": str(e),
        }

    finally:
        conn.close()

def obtener_turnos_calculados(cur, fecha: int):
    cur.execute("""
        SELECT DISTINCT TRIM(q.c_tsorteo)
        FROM premios p
        JOIN quiniela_exp q
            ON q.id = p.quiniela_exp_id
        WHERE p.fecha_sorteo = %s
        ORDER BY TRIM(q.c_tsorteo)
    """, (fecha,))

    return [row[0] for row in cur.fetchall()]

def obtener_resumen_por_fecha(fecha: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                fecha_sorteo,
                turno,
                codigo_extracto,
                sorteo,
                cupones_jugados,
                recaudacion,
                importe_premiados,
                comision,
                utilidad,
                porcentaje_utilidad,
                apuestas_premiadas,
                archivo_aciertos_dbf,
                cupones_ganadores_unicos,
                cupones_ganadores_dbf,
                fecha_calculo
            FROM resumen_auditoria
            WHERE fecha_sorteo = %s
            ORDER BY
                CASE turno
                    WHEN 'PV' THEN 1
                    WHEN 'PR' THEN 2
                    WHEN 'M' THEN 3
                    WHEN 'V' THEN 4
                    WHEN 'N' THEN 5
                    ELSE 99
                END,
                codigo_extracto
        """, (fecha,))

        rows = cur.fetchall()

        turnos = {}

        for row in rows:
            (
                fecha_sorteo,
                turno,
                codigo_extracto,
                sorteo,
                cupones_jugados,
                recaudacion,
                importe_premiados,
                comision,
                utilidad,
                porcentaje_utilidad,
                apuestas_premiadas,
                archivo_aciertos_dbf,
                cupones_ganadores_unicos,
                cupones_ganadores_dbf,
                fecha_calculo,
            ) = row

            if turno not in turnos:
                turnos[turno] = {
                    "turno": turno,
                    "cupones_ganadores_unicos": int(cupones_ganadores_unicos),
                    "cupones_ganadores_dbf": int(cupones_ganadores_dbf),
                    "fecha_calculo": str(fecha_calculo),
                    "reportes": []
                }

            turnos[turno]["reportes"].append({
                "codigo_extracto": int(codigo_extracto),
                "sorteo": sorteo,
                "cupones_jugados": int(cupones_jugados),
                "recaudacion": float(recaudacion),
                "importe_premiados": float(importe_premiados),
                "comision": float(comision),
                "utilidad": float(utilidad),
                "porcentaje_utilidad": float(porcentaje_utilidad),
                "apuestas_premiadas": int(apuestas_premiadas),
                "archivo_aciertos_dbf": int(archivo_aciertos_dbf),
            })

        return {
            "ok": True,
            "fecha": fecha,
            "origen": "resumen_auditoria",
            "turnos": list(turnos.values())
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

    finally:
        cur.close()
        conn.close()

