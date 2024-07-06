from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.paragraph import Paragraph
from functools import partial
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from datetime import datetime, timedelta
from reportlab.lib import colors


def header(canvas, doc, content):
    canvas.saveState()
    w, h = content.wrap(doc.width, doc.topMargin)
    content.drawOn(canvas, doc.leftMargin, doc.height + doc.bottomMargin + doc.topMargin - h)
    canvas.restoreState()

def footer(canvas, doc, content):
    canvas.saveState()
    w, h = content.wrap(doc.width, doc.bottomMargin)
    content.drawOn(canvas, doc.leftMargin, h)
    canvas.restoreState()

def header_and_footer(canvas, doc, header_content, footer_content):
    header(canvas, doc, header_content)
    footer(canvas, doc, footer_content)

def get_datetime():
    # Obtener la fecha y hora actual
    now = datetime.now() + timedelta(hours=-5)
    # Mapeo de nombres de meses en inglés a español
    meses_ingles_a_espanol = {
        "January": "enero",
        "February": "febrero",
        "March": "marzo",
        "April": "abril",
        "May": "mayo",
        "June": "junio",
        "July": "julio",
        "August": "agosto",
        "September": "septiembre",
        "October": "octubre",
        "November": "noviembre",
        "December": "diciembre"
    }
    # Formatear la fecha y hora de emisión
    emision = "<b>Hora y fecha de emision:</b> " + now.strftime("%d de %B del %Y, %H:%M")
    for mes_ingles, mes_espanol in meses_ingles_a_espanol.items():
        emision = emision.replace(mes_ingles, mes_espanol)
    #
    # Formatear dia anterior
    anterior = (now + timedelta(days=-1)).strftime("%d de %B del %Y (07H00)")
    for mes_ingles, mes_espanol in meses_ingles_a_espanol.items():
        anterior = anterior.replace(mes_ingles, mes_espanol)
    # Formatear dia actual
    actual = (now).strftime("%d de %B del %Y (07H00)")
    for mes_ingles, mes_espanol in meses_ingles_a_espanol.items():
        actual = actual.replace(mes_ingles, mes_espanol)
    # Formatear dia futuro
    futuro = (now + timedelta(days=1)).strftime("%d de %B del %Y (07H00)")
    for mes_ingles, mes_espanol in meses_ingles_a_espanol.items():
        futuro = futuro.replace(mes_ingles, mes_espanol)
    #
    # Calcular la vigencia para 24 horas
    inicio_vigencia = now.strftime("desde 07:00 del %d de %B")
    fin_vigencia = (now + timedelta(days=1)).strftime("hasta las 07:00 del %d de %B del %Y")
    for mes_ingles, mes_espanol in meses_ingles_a_espanol.items():
        inicio_vigencia = inicio_vigencia.replace(mes_ingles, mes_espanol)
        fin_vigencia = fin_vigencia.replace(mes_ingles, mes_espanol)
    #
    # Formatear la vigencia
    vigencia = f"<b>Vigencia:</b> {inicio_vigencia} {fin_vigencia}"
    return(emision, vigencia, anterior, actual, futuro)


def agregar_tabla(datos):
    datos_tabla = [datos.columns.tolist()] + datos.values.tolist()
    tabla = Table(datos_tabla)
    tabla.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey),
                               ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                               ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                               ('FONTSIZE', (0, 0), (-1, -1), 7),
                               ('BOTTOMPADDING', (0,0), (-1,0), 2),
                               ('BACKGROUND', (0,1), (-1,-1), colors.white),
                               ('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    return(tabla)


def report(filename, pacum, forecast, asm, tables):
    # Vars
    header_path = "report_header.png"
    footer_path = "report_footer.png"
    titulo = "<b>Boletín Hidrometeorológico Especial Baños</b>"
    emision, vigencia, anterior, actual, futuro = get_datetime()
    parrafo_1 = "La <b>DIRECCIÓN DE PRONÓSTICOS Y ALERTAS HIDROMETEOROLÓGICAS DEL INAMHI</b>, basándose en la información obtenida de la plataforma INAMHI GEOGLOWS emite el siguiente boletín de vigilancia y predicción de condiciones hidrometeorológicas:"
    subtitulo_1 = "<b>Precipitación acumulada diaria</b>"
    subtitulo_2 = "<b>Pronóstico de precipitación</b>"
    subtitulo_3 = "<b>Humedad del suelo</b>"
    subtitulo_4 = "<b>Pronóstico hidrológico (GEOGLOWS)</b>"
    parrafo_2 = f"De acuerdo con los datos del hidroestimador satelital <b>PERSIANN PDIR Now</b>, en la zona de interés se registró una precipitación media de <b>{pacum} mm</b> entre el <b>{anterior}</b> y el <b>{actual}.</b>"
    parrafo_3 = f"Según los datos del <b>modelo WRF (INAMHI)</b>, se pronostica una precipitación media de <b>{forecast} mm</b> en la zona de interés, entre el <b>{actual}</b> y el <b>{futuro}.</b>"
    parrafo_4 = f"De acuerdo con la plataforma Flash Flood Guidance System <b>(FFGS)</b>, en la zona de interés se registró una humedad media del suelo de <b>{100*asm} %</b> entre el <b>{anterior}</b> y el <b>{actual}.</b>"
    # Configurar estilos
    estilos = getSampleStyleSheet()
    #
    estilo_titulo = ParagraphStyle(
        name = 'Title',
        fontSize = 14,
        textColor = colors.Color(31/255, 73/255, 125/255),
        alignment = TA_CENTER)
    #
    estilo_subtitulo = ParagraphStyle(
        name = 'Subtitle',
        fontSize = 11,
        textColor = colors.Color(31/255, 73/255, 125/255),
        alignment = TA_LEFT,
        spaceAfter = 4)
    #
    estilo_fecha = ParagraphStyle(
        name = 'Dates',
        fontSize = 9,
        alignment = TA_CENTER,
        spaceBefore = 3,
        spaceAfter = 3)
    #
    estilo_parrafo = ParagraphStyle(
        name = 'P01',
        fontSize = 9,
        alignment = TA_CENTER,
        spaceBefore = 5,
        spaceAfter = 5,
        leading = 15)
    #
    estilo_parrafo2 = ParagraphStyle(
        name = 'P02',
        fontSize = 9,
        alignment = TA_JUSTIFY,
        spaceBefore = 5,
        spaceAfter = 5,
        leading = 15)
    #
    # Crear el documento PDF
    doc = SimpleDocTemplate(filename, pagesize=letter)
    #
    # Definir el encabezado y pie de pagina
    header_content = Image(header_path, width=doc.width, height=2.5*cm)
    footer_content = Image(footer_path, width=doc.width, height=1.5*cm)
    #
    # Agregar elementos al contenido del PDF
    elementos = [
        Paragraph(titulo, estilo_titulo),
        Spacer(1, 12),
        Paragraph(emision, estilo_fecha),
        Paragraph(vigencia, estilo_fecha),
        Spacer(1, 10),
        Paragraph(parrafo_1, estilo_parrafo),
        Spacer(1, 10),
        Paragraph(subtitulo_1, estilo_subtitulo),
        Image("pacum_sat.png", width=doc.width, height=5*cm),
        Image("pacum24.png", width=14*cm, height=0.7*cm),
        Paragraph(parrafo_2, estilo_parrafo2),
        Spacer(1, 20),
        Paragraph(subtitulo_2, estilo_subtitulo),
        Image("pacum_wrf.png", width=doc.width, height=5*cm),
        Image("pacum24.png", width=14*cm, height=0.7*cm),
        Paragraph(parrafo_3, estilo_parrafo2),
        ##
        PageBreak(),
        Paragraph(subtitulo_3, estilo_subtitulo),
        Image("asm.png", width=doc.width, height=5*cm),
        Image("soilmoisture_legend.png", width=10*cm, height=1*cm),
        Paragraph(parrafo_4, estilo_parrafo2),
        Spacer(1, 30),
        Paragraph(subtitulo_4, estilo_subtitulo),
        Paragraph("Con base en la información del modelo hidrológico GEOGLOWS, se emite el siguiente pronóstico hidrológico", estilo_parrafo2),
        Paragraph("<b>1. Rio Patate</b>", estilo_parrafo2),
        Image("forecast_9028087.png", width=doc.width, height=4*cm),
        Image("leyenda.png", width=10*cm, height=1*cm),
        Paragraph("<b>Tabla 1.</b> Caudales pronosticados para el río Patate", estilo_parrafo),
        agregar_tabla(tables[0]),

        ##
        PageBreak(),
        Paragraph("<b>2. Rio Chambo</b>", estilo_parrafo2),
        Image("forecast_9028483.png", width=doc.width, height=4*cm),
        Image("leyenda.png", width=10*cm, height=1*cm),
        Paragraph("<b>Tabla 2.</b> Caudales pronosticados para el río Chambo", estilo_parrafo),
        agregar_tabla(tables[1]),
        Spacer(1, 20),

        Paragraph("<b>3. Rio Verde Chico</b>", estilo_parrafo2),
        Image("forecast_9028041.png", width=doc.width, height=4*cm),
        Image("leyenda.png", width=10*cm, height=1*cm),
        Paragraph("<b>Tabla 3.</b> Caudales pronosticados para el río Verde Chico", estilo_parrafo),
        agregar_tabla(tables[2]),

        ##
        PageBreak(),
        Paragraph("<b>4. Rio Verde</b>", estilo_parrafo2),
        Image("forecast_9028088.png", width=doc.width, height=4*cm),
        Image("leyenda.png", width=10*cm, height=1*cm),
        Paragraph("<b>Tabla 4.</b> Caudales pronosticados para el río Verde", estilo_parrafo),
        agregar_tabla(tables[3]),
        Spacer(1, 20),

        Paragraph("<b>5. Rio Topo</b>", estilo_parrafo2),
        Image("forecast_9028099.png", width=doc.width, height=4*cm),
        Image("leyenda.png", width=10*cm, height=1*cm),
        Paragraph("<b>Tabla 5.</b> Caudales pronosticados para el río Topo", estilo_parrafo),
        agregar_tabla(tables[4]),

        ##
        PageBreak(),
        Paragraph("<b>6. Rio Pastaza (tramo 1)</b>", estilo_parrafo2),
        Image("forecast_9028091.png", width=doc.width, height=4*cm),
        Image("leyenda.png", width=10*cm, height=1*cm),
        Paragraph("<b>Tabla 6.</b> Caudales pronosticados del tramo 1 del río Pastaza", estilo_parrafo),
        agregar_tabla(tables[5]),
        Spacer(1, 20),

        Paragraph("<b>7. Rio Pastaza (tramo 2)</b>", estilo_parrafo2),
        Image("forecast_9028095.png", width=doc.width, height=4*cm),
        Image("leyenda.png", width=10*cm, height=1*cm),
        Paragraph("<b>Tabla 7.</b> Caudales pronosticados del tramo 2 del río Pastaza", estilo_parrafo),
        agregar_tabla(tables[6]),

        ##
        PageBreak(),
        Paragraph("<b>8. Rio Pastaza (tramo 3)</b>", estilo_parrafo2),
        Image("forecast_9028125.png", width=doc.width, height=4*cm),
        Image("leyenda.png", width=10*cm, height=1*cm),
        Paragraph("<b>Tabla 8.</b> Caudales pronosticados del tramo 3 del río Pastaza", estilo_parrafo),
        agregar_tabla(tables[5]),

        ]
    #
    # Contruir el pdf
    doc.build(
        elementos, 
        onFirstPage=partial(header_and_footer, header_content=header_content, footer_content=footer_content), 
        onLaterPages=partial(header_and_footer, header_content=header_content, footer_content=footer_content))

