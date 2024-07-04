from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.paragraph import Paragraph
from functools import partial
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
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
    anterior = (now + timedelta(days=-1)).strftime("%d de %B del %Y")
    for mes_ingles, mes_espanol in meses_ingles_a_espanol.items():
        anterior = anterior.replace(mes_ingles, mes_espanol)
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
    return(emision, vigencia, anterior)


def agregar_tabla(datos):
    datos_tabla = [datos.columns.tolist()] + datos.values.tolist()
    tabla = Table(datos_tabla)
    tabla.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey),
                               ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                               ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                               ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                               ('BOTTOMPADDING', (0,0), (-1,0), 3),
                               ('BACKGROUND', (0,1), (-1,-1), colors.white),
                               ('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    return(tabla)


def report(filename, pacum):
    # Vars
    header_path = "report_header.png"
    footer_path = "report_footer.png"
    titulo = "<b>Boletín Hidrometeorológico Especial Paute</b>"
    emision, vigencia, anterior = get_datetime()
    parrafo_1 = "La <b>DIRECCIÓN DE PRONÓSTICOS Y ALERTAS HIDROMETEOROLÓGICAS DEL INAMHI</b>, basándose en la información obtenida de la plataforma INAMHI GEOGLOWS emite el siguiente boletín de vigilancia y predicción de condiciones hidrometeorológicas:"
    subtitulo_1 = "<b>Precipitación acumulada diaria</b>"
    parrafo_2 = f"De acuerdo con los datos del hidroestimador satelital PERSIANN PDIR Now, la precipitación media registrada en la Cuenca del río Paute durante el {anterior}, fue de {pacum} mm. A continuación se presenta un desglose de la precipitación media por subcuencas."
    #
    # Configurar estilos
    estilos = getSampleStyleSheet()
    #
    estilo_titulo = ParagraphStyle(
        name = 'Title',
        fontSize = 18,
        textColor = colors.Color(31/255, 73/255, 125/255),
        alignment = TA_CENTER)
    #
    estilo_subtitulo = ParagraphStyle(
        name = 'Subtitle',
        fontSize = 14,
        textColor = colors.Color(31/255, 73/255, 125/255),
        alignment = TA_CENTER)
    #
    estilo_fecha = ParagraphStyle(
        name = 'Dates',
        fontSize = 10,
        alignment = TA_CENTER,
        spaceBefore = 5,
        spaceAfter = 5)
    #
    estilo_parrafo = ParagraphStyle(
        name = 'P01',
        fontSize = 10,
        alignment = TA_CENTER,
        spaceBefore = 5,
        spaceAfter = 5,
        leading = 16)
    #
    estilo_parrafo2 = ParagraphStyle(
        name = 'P02',
        fontSize = 10,
        alignment = TA_JUSTIFY,
        spaceBefore = 5,
        spaceAfter = 5,
        leading = 16)
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
        Spacer(1, 14),
        Paragraph(emision, estilo_fecha),
        Paragraph(vigencia, estilo_fecha),
        Spacer(1, 14),
        Paragraph(parrafo_1, estilo_parrafo),
        Spacer(1, 14),
        Paragraph(subtitulo_1, estilo_subtitulo),
        Spacer(1, 10),
        Image("pacum_sat.png", width=doc.width, height=8*cm),
        Image("pacum24.png", width=12*cm, height=1.2*cm),
        ]
    #
    # Contruir el pdf
    doc.build(
        elementos, 
        onFirstPage=partial(header_and_footer, header_content=header_content, footer_content=footer_content), 
        onLaterPages=partial(header_and_footer, header_content=header_content, footer_content=footer_content))

