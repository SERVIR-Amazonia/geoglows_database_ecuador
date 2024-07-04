import requests
from datetime import datetime
import xml.etree.ElementTree as ET


def get_layer_wrf_name(date):
    url = "http://ec2-3-211-227-44.compute-1.amazonaws.com/geoserver/wrf-precipitation/wms?service=WMS&request=GetCapabilities"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    query = date.strftime("%Y-%m-%d00Z-24H")
    # Define el namespace
    namespace = {'wms': 'http://www.opengis.net/wms'}
    # Encuentra todos los elementos 'Layer' dentro del namespace
    layers = []
    for layer in root.findall('.//wms:Layer', namespace):
        layer_name_elem = layer.find('wms:Name', namespace)
        if layer_name_elem is not None:
            layer_name = layer_name_elem.text
            if layer_name.startswith(query):
                layers.append(layer_name)
    return(layers)



def extraer_fechas(cadena):
    # Extraer las dos fechas de la cadena
    fecha1_str = cadena[:10]
    fecha2_str = cadena[-12:-4]
    # Convertir las fechas a objetos datetime
    fecha1 = datetime.strptime(fecha1_str, "%Y-%m-%d")
    fecha2 = datetime.strptime(fecha2_str, "%Y%m%d")
    # Formatear las fechas como strings en el formato deseado
    fecha1_formateada = fecha1.strftime("%Y-%m-%d")
    fecha2_formateada = fecha2.strftime("%Y-%m-%d")
    return fecha1_formateada, fecha2_formateada