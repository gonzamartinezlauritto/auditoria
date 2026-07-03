from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import cm
from decimal import Decimal, ROUND_HALF_UP
import psycopg2
from legacy.scripts_viejos.config import DB_CONFIG


FECHA = 20260601
EXTRACTOS = [50, 51, 52, 53, 54, 55, 56]

DEBUG_ACTIVO = False
DEBUG_CUPONES = set()


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


def redondear_a_diez_centavos(valor):
    valor = Decimal(str(valor or 0))
    return (
        (valor / Decimal("0.10"))
        .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        * Decimal("0.10")
    ).quantize(Decimal("0.01"))


def formatear(valor):
    valor = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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

    # Si la base es a cabeza, el detalle se desplaza.
    # 0-5 pasa a 2-6, 0-10 pasa a 2-11.
    if base_desde == 0 and base_hasta == 1:
        return 2, min(det_hasta + 1, 20)

    # Si ambos van a los 10, quedan ambos 1-10.
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


def calcular_extracto(conn, fecha, cod):
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
          AND n_codext = %s
          AND COALESCE(c_ecupon, '') = 'N'
          AND COALESCE(n_nodef, 0) <> 1
        ORDER BY n_agent, n_subag, n_maqui, n_cupon, n_linea, id
    """, (fecha, cod))

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

        # ============================
        # REDOBLONA
        # ============================
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

            premio_base_unit = calcular_premio(
                importe,
                mult_base,
                puestos_base
            )

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

            # Regla final:
            # base y detalle no pueden usar el mismo puesto.
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

        # ============================
        # NORMALES
        # ============================
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

        # ============================
        # APROXIMADOS
        # ============================
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

    # ============================
    # RESUMEN PARA REPORTE
    # ============================

    cur.execute("""
        SELECT COALESCE(SUM(n_impapos), 0)
        FROM quiniela_exp
        WHERE n_fsorteo = %s
          AND n_codext = %s
          AND COALESCE(c_ecupon, '') = 'N'
          AND COALESCE(n_nodef, 0) <> 1
          AND n_impapos > 0
    """, (fecha, cod))
    total_recaudado = (Decimal(str(cur.fetchone()[0] or 0)) / Decimal("100")).quantize(Decimal("0.01"))

    cur.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT n_agent, n_subag, n_maqui, n_cupon
            FROM quiniela_exp
            WHERE n_fsorteo = %s
              AND n_codext = %s
              AND COALESCE(c_ecupon, '') = 'N'
              AND COALESCE(n_nodef, 0) <> 1
            GROUP BY n_agent, n_subag, n_maqui, n_cupon
        ) t
    """, (fecha, cod))
    cupones_jugados = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT COALESCE(SUM(premio_total), 0)
        FROM premios
        WHERE fecha_sorteo = %s
          AND codigo_extracto = %s
    """, (fecha, cod))
    total_final = redondear_a_diez_centavos(Decimal(str(cur.fetchone()[0] or 0)) / Decimal("100"))

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
            AND p.codigo_extracto = %s
            AND p.premio_total <> 0
            GROUP BY
                q.n_agent,
                q.n_subag,
                q.n_maqui,
                q.n_cupon
        ) t
    """, (fecha, cod))
    cant_premios = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT COUNT(*)
        FROM aciertos_dbf
        WHERE fecha_sorteo = %s
          AND codigo_extracto = %s
    """, (fecha, cod))
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


def imprimir_reporte(reportes, cupones_ganadores_unicos):

    ORDEN_CODIGOS = [52, 56, 51, 54, 50, 55, 53]

    orden_map = {
        codigo: i
        for i, codigo in enumerate(ORDEN_CODIGOS)
    }

    reportes = sorted(
        reportes,
        key=lambda x: orden_map.get(x["codigo_extracto"], 999)
    )

    print("\nRECAUDACIÓN POR EXTRACTO")
    print(f"Fecha Desde/Hasta: {FECHA} hasta {FECHA}")
    print("-" * 115)

    print(
        f"{'Sorteo':35}"
        f"{'Cupones':>12}"
        f"{'Recaudación':>20}"
        f"{'Importe Premios':>22}"
        f"{'Apuestas Premiadas':>24}"
    )

    print("-" * 115)

    total_cupones = 0
    total_recaudacion = Decimal("0.00")
    total_premios = Decimal("0.00")
    total_apuestas = 0

    for r in reportes:
        total_cupones += r["cupones_jugados"]
        total_recaudacion += r["recaudacion"]
        total_premios += r["importe_premiados"]
        total_apuestas += r["apuestas_premiadas"]

        print(
            f"{r['sorteo'][:35]:35}"
            f"{r['cupones_jugados']:>12}"
            f"{formatear(r['recaudacion']):>20}"
            f"{formatear(r['importe_premiados']):>22}"
            f"{r['apuestas_premiadas']:>24}"
        )

    print("-" * 115)

    print(
        f"{'TOTALES GENERALES':35}"
        f"{total_cupones:>12}"
        f"{formatear(total_recaudacion):>20}"
        f"{formatear(redondear_a_diez_centavos(total_premios)):>22}"
        f"{total_apuestas:>24}"
    )
    print("\n==============================")
    print(f"CUPONES GANADORES ÚNICOS: {cupones_ganadores_unicos}")
    print("==============================")

def generar_pdf_control_aciertos(
    reportes,
    fecha,
    cupones_ganadores_unicos,
    cupones_ganadores_dbf,
    archivo_salida="control_aciertos.pdf"
):
    doc = SimpleDocTemplate(
        archivo_salida,
        pagesize=landscape(A3),
        rightMargin=1 * cm,
        leftMargin=1 * cm,
        topMargin=1 * cm,
        bottomMargin=1 * cm,
    )

    ORDEN_CODIGOS = [52, 56, 51, 54, 50, 55, 53]
    orden_map = {codigo: i for i, codigo in enumerate(ORDEN_CODIGOS)}
    reportes = sorted(reportes, key=lambda x: orden_map.get(x["codigo_extracto"], 999))

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        alignment=1,
        spaceAfter=18,
    )

    normal_bold = ParagraphStyle(
        "normal_bold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
    )

    cell_style = ParagraphStyle(
        "cell",
        parent=styles["Normal"],
        fontSize=16,
        leading=20,
    )

    header_style = ParagraphStyle(
        "header",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        alignment=1,
        leading=16,
    )

    titulo_tabla_style = ParagraphStyle(
        "titulo_tabla",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        alignment=1,
        spaceAfter=14,
    )

    story = []

    story.append(Paragraph("Control de Aciertos - Quiniela", title_style))
    story.append(Spacer(1, 8))

    fecha_str = f"{str(fecha)[6:8]}/{str(fecha)[4:6]}/{str(fecha)[0:4]}"

    encabezado = [
        [Paragraph("Evento:", normal_bold), Paragraph("LA PREVIA", normal_bold)],
        [Paragraph("Fecha de Sorteo:", normal_bold), Paragraph(fecha_str, normal_bold)],
    ]

    t_enc = Table(encabezado, colWidths=[5 * cm, 10 * cm])
    t_enc.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_enc)

    story.append(Spacer(1, 24))
    story.append(Paragraph("RESULTADOS FINALES", titulo_tabla_style))
    story.append(Spacer(1, 8))

    data = [
        [
            "", "", "", "", "", "",
            Paragraph("Cupones Premiados", header_style),
            "",
        ],
        [
            Paragraph("Extracto", header_style),
            Paragraph("Importe<br/>Recaudación", header_style),
            Paragraph("Importe<br/>Aciertos", header_style),
            Paragraph("Importe<br/>Comisión", header_style),
            Paragraph("Importe<br/>Utilidad", header_style),
            Paragraph("%<br/>Util/Rec.", header_style),
            Paragraph("Archivo<br/>FrontEnd", header_style),
            Paragraph("Generados<br/>Auditoría", header_style),
        ],
    ]

    total_recaudacion = Decimal("0.00")
    total_aciertos = Decimal("0.00")
    total_comision = Decimal("0.00")
    total_utilidad = Decimal("0.00")
    total_archivo_dbf = 0
    total_auditoria = 0

    for r in reportes:
        recaudacion = Decimal(str(r["recaudacion"]))
        aciertos = Decimal(str(r["importe_premiados"]))
        archivo_dbf = int(r.get("archivo_aciertos_dbf", 0))
        generados_auditoria = int(r["apuestas_premiadas"])

        comision = (recaudacion * Decimal("0.20")).quantize(Decimal("0.01"))
        utilidad = (recaudacion - aciertos - comision).quantize(Decimal("0.01"))

        porcentaje = Decimal("0.00")
        if recaudacion > 0:
            porcentaje = ((utilidad / recaudacion) * Decimal("100")).quantize(Decimal("0.01"))

        total_recaudacion += recaudacion
        total_aciertos += aciertos
        total_comision += comision
        total_utilidad += utilidad
        total_archivo_dbf += archivo_dbf
        total_auditoria += generados_auditoria

        data.append([
            Paragraph(r["sorteo"], cell_style),
            formatear(recaudacion),
            formatear(aciertos),
            formatear(comision),
            formatear(utilidad),
            str(porcentaje).replace(".", ","),
            archivo_dbf,
            generados_auditoria,
        ])

    data.append([
        Paragraph("Totales", header_style),
        formatear(total_recaudacion),
        formatear(total_aciertos),
        formatear(total_comision),
        formatear(total_utilidad),
        "",
        total_archivo_dbf,
        total_auditoria,
    ])

    celeste = colors.HexColor("#B8E6F8")

    table = Table(
        data,
        colWidths=[
            7.0 * cm,
            4.8 * cm,
            4.8 * cm,
            4.5 * cm,
            4.8 * cm,
            3.0 * cm,
            3.4 * cm,
            3.4 * cm,
        ],
        repeatRows=2,
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 1), (-1, -1), 0.6, colors.black),

        ("SPAN", (6, 0), (7, 0)),
        ("ALIGN", (6, 0), (7, 0), "CENTER"),
        ("FONTNAME", (6, 0), (7, 0), "Helvetica-Bold"),
        ("FONTSIZE", (6, 0), (7, 0), 13),

        ("BACKGROUND", (0, 1), (-1, 1), celeste),
        ("BACKGROUND", (0, -1), (-1, -1), celeste),

        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),

        ("ALIGN", (1, 2), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (0, -1), (-1, -1), "CENTER"),

        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        # HEADER
        ("FONTSIZE", (0, 1), (-1, 1), 14),
        # DATOS
        ("FONTSIZE", (0, 2), (-1, -2), 16),
        # TOTALES
        ("FONTSIZE", (0, -1), (-1, -1), 16),

        ("TOPPADDING", (0, 1), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
    ]))

    story.append(table)
    story.append(Spacer(1, 16))

    tabla_cupones_unicos = Table(
        [
            [
                Paragraph("Cupones Ganadores Únicos", header_style),
                Paragraph("Archivo<br/>FrontEnd", header_style),
                Paragraph("Auditoría", header_style),
            ],
            [
                "Totales",
                str(cupones_ganadores_dbf),
                str(cupones_ganadores_unicos),
            ],
        ],
        colWidths=[8 * cm, 4.5 * cm, 4.5 * cm],
    )

    tabla_cupones_unicos.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), celeste),
        ("BACKGROUND", (0, -1), (-1, -1), celeste),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),
        ("FONTSIZE", (0, 1), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))

    story.append(tabla_cupones_unicos)

    doc.build(story)

    print(f"PDF generado: {archivo_salida}")

def obtener_cupones_ganadores_unicos(conn, fecha):
    cur = conn.cursor()

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
              AND p.premio_total <> 0
            GROUP BY
                q.n_agent,
                q.n_subag,
                q.n_maqui,
                q.n_cupon
        ) t
    """, (fecha,))

    return cur.fetchone()[0] or 0

def obtener_cupones_ganadores_unicos_dbf(conn, fecha):
    cur = conn.cursor()

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
            GROUP BY
                agencia,
                subagencia,
                nromaquina,
                numero
        ) t
    """, (fecha,))

    return cur.fetchone()[0] or 0

def main():
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        reportes = []

        for codigo_extracto in EXTRACTOS:
            print(f"Calculando extracto {codigo_extracto}...")
            resultado = calcular_extracto(conn, FECHA, codigo_extracto)
            reportes.append(resultado)

        conn.commit()
        
        cupones_ganadores_unicos = obtener_cupones_ganadores_unicos(conn, FECHA)
        cupones_ganadores_dbf = obtener_cupones_ganadores_unicos_dbf(conn, FECHA)

        imprimir_reporte(reportes, cupones_ganadores_unicos)
        generar_pdf_control_aciertos(
            reportes,
            FECHA,
            cupones_ganadores_unicos,
            cupones_ganadores_dbf,
            "control_aciertos_quiniela.pdf"
        )

    except Exception as e:
        conn.rollback()
        print("ERROR:", e)

    finally:
        conn.close()


if __name__ == "__main__":
    main()