from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, PageTemplate, Image, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.frames import Frame
from reportlab.platypus.paragraph import Paragraph
from functools import partial
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
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
    # Calcular la vigencia para 24 horas
    inicio_vigencia = now.strftime("desde 07:00 del %d de %B")
    fin_vigencia = (now + timedelta(days=1)).strftime("hasta las 07:00 del %d de %B del %Y")
    for mes_ingles, mes_espanol in meses_ingles_a_espanol.items():
        inicio_vigencia = inicio_vigencia.replace(mes_ingles, mes_espanol)
        fin_vigencia = fin_vigencia.replace(mes_ingles, mes_espanol)
    # Formatear la vigencia
    vigencia = f"<b>Vigencia:</b> {inicio_vigencia} {fin_vigencia}"
    return(emision, vigencia)


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


def report(filename, pacum, pacum_table):
    # Vars
    header_path = "report_header.png"
    footer_path = "report_footer.png"
    titulo = "Boletín Hidrometeorológico Especial Paute"
    emision, vigencia = get_datetime()
    parrafo_1 = "La <b>DIRECCIÓN DE PRONÓSTICOS Y ALERTAS HIDROMETEOROLÓGICAS DEL INAMHI </b>, basándose en la información obtenida de la plataforma INAMHI GEOGLOWS emite el siguiente boletín de vigilancia y predicción de condiciones hidrometeorológicas:"
    subtitulo_1 = "<b>Precipitación acumulada diaria (GPM IMERG)</b>"
    parrafo_2 = f"Precipitacion media en la Cuenca del río Paute: {pacum} mm"
    #
    # Configurar estilos
    estilos = getSampleStyleSheet()
    estilo_titulo = estilos["Title"]
    estilo_parrafo = estilos["Normal"]
    estilo_parrafo.alignment = TA_CENTER
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
        Spacer(1, 8),
        Paragraph(titulo, estilo_titulo),
        Spacer(1, 8),
        Paragraph(emision, estilo_parrafo),
        Paragraph(vigencia, estilo_parrafo),
        Spacer(1, 20),
        Paragraph(parrafo_1, estilo_parrafo),
        Spacer(1, 24),
        Paragraph(subtitulo_1, estilo_parrafo),
        Spacer(1, 5),
        Paragraph(parrafo_2, estilo_parrafo),
        Spacer(1, 5),
        Image("pacum.png", width=doc.width, height=8*cm),
        Image("pacum24.png", width=12*cm, height=1.2*cm),
        Spacer(1, 12),
        agregar_tabla(pacum_table),
        PageBreak(),
        Paragraph("<b>Pronóstico hidrológico: Río Paute (en Paute)</b>", estilo_parrafo),
        Image("paute_en_paute.png", width=doc.width, height=8*cm),
        
        
    ]
    #
    # Contruir el pdf
    doc.build(
        elementos, 
        onFirstPage=partial(header_and_footer, header_content=header_content, footer_content=footer_content), 
        onLaterPages=partial(header_and_footer, header_content=header_content, footer_content=footer_content))





#import pandas as pd
# Datos de ejemplo
#datos = {
#    'Subcuenca': ['Cuenca 1', 'Cuenca 2', 'Cuenca 3'],
#    'Precipitacion media (mm)': [10.5, 20.3, 15.8]
#}
#df = pd.DataFrame(datos)


#filename = "prueba-final.pdf"
#report(filename, pacum=0.5, pacum_table=df)





