import datetime
import time
import urllib.request
from urllib.error import HTTPError
import pandas as pd
import requests

import os
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_bounds
from rasterio.features import geometry_mask
import geopandas as gpd
from shapely.geometry import box
from fiona.crs import from_epsg

from hs_restclient import HydroShare, HydroShareAuthBasic
from dotenv import load_dotenv


# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("tethys_apps_ecuador/geoglows_database_ecuador")

# Import enviromental variables
load_dotenv()
NASA_USER = os.getenv('NASA_USER')
NASA_PASS = os.getenv('NASA_PASS')
HS_USER = os.getenv('HS_USER')
HS_PASS = os.getenv('HS_PASS')
HS_IDRS = os.getenv('HS_ID01')
PYTHON_PATH = os.getenv('PYTHON_PATH')


# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("data/gpm_imerg")


def get_imerg_pacum(temp):
    try:
        ndays = int(temp/24)
        # Generar la fecha actual
        actual_date = datetime.datetime.now() + datetime.timedelta(hours=-5)
        actual_year = actual_date.strftime("%Y")
        actual_month = actual_date.strftime("%m")
        #
        # Descargar los nombres de archivos existentes
        url = "https://jsimpsonhttps.pps.eosdis.nasa.gov/text/imerg/gis/early/"
        #url = "https://jsimpsonhttps.pps.eosdis.nasa.gov/text/imerg/gis/early/{0}/{1}/"
        #url = url.format(actual_year, actual_month)
        #
        # Descargar el archivo con los nombres de los recursos
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, NASA_USER, NASA_PASS)
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(handler)
        urllib.request.install_opener(opener)
        response = urllib.request.urlopen(url)
        with open("files.txt", "wb") as output_file:
            output_file.write(response.read())
        #
        # Leer el archivo
        files = pd.read_table("files.txt")
        files.columns = ['files']
        #
        # Generar el rango de fechas
        fecha_final = actual_date 
        fecha_final = pd.to_datetime(fecha_final).floor('H')
        fecha_inicial = fecha_final + datetime.timedelta(days=-ndays) 
        #
        # Definir el intervalo de tiempo (en segundos)
        intervalo = 30*60
        #
        # Crear una lista de tuplas que representen los pares de inicio y final
        pares_fecha = []
        while fecha_inicial <= fecha_final:
            fecha_final_intervalo = fecha_inicial + datetime.timedelta(seconds=intervalo - 1)
            pares_fecha.append((fecha_inicial, fecha_final_intervalo))
            fecha_inicial = fecha_final_intervalo + datetime.timedelta(seconds=1)
        #
        # Crear un DataFrame a partir de la lista de pares de fecha
        df = pd.DataFrame(pares_fecha, columns=['start', 'finish'])
        #
        # Descargar los datos
        for i in range(len(df.start)):
            try:
                start_year = df.start[i].strftime("%Y")
                start_month = df.start[i].strftime("%m")
                start_day = df.start[i].strftime("%d")
                start_hour = df.start[i].strftime("%H")
                start_minute = df.start[i].strftime("%M")
                start_second = df.start[i].strftime("%S")
                finish_hour = df.finish[i].strftime("%H")
                finish_minute = df.finish[i].strftime("%M")
                finish_second = df.finish[i].strftime("%S")
                #source = "/imerg/gis/early/{0}/{1}/3B-HHR-E.MS.MRG.3IMERG.{0}{1}{2}-S{3}{4}{5}-E{6}{7}{8}".format(start_year,start_month,start_day,start_hour,start_minute,start_second,finish_hour,finish_minute,finish_second)
                source = "/imerg/gis/early/3B-HHR-E.MS.MRG.3IMERG.{0}{1}{2}-S{3}{4}{5}-E{6}{7}{8}".format(start_year,start_month,start_day,start_hour,start_minute,start_second,finish_hour,finish_minute,finish_second)
                resultado = files[files['files'].str.contains(source)]
                resultado = resultado[resultado['files'].str.contains("30min.tif")].iloc[0,0]
                url = "https://jsimpsonhttps.pps.eosdis.nasa.gov{0}".format(resultado)
                # Authenticacion
                auth = (NASA_USER, NASA_PASS)
                response = requests.get(url, auth=auth)
                nombre_archivo = df.start[i].strftime("%Y_%m_%d_%H_%M.tif")
                if response.status_code == 200:
                    with open(nombre_archivo, 'wb') as f:
                        f.write(response.content)
                    print(f'Descarga exitosa: {nombre_archivo}')
                else:
                    print(f'Error al descargar: Código de estado {response.status_code}')
            except Exception as e:
                print("Conexion no permitida")
                print(e)
                time.sleep(10)
        #
        # Lista para almacenar los nombres de los archivos GeoTIFF
        archivos_geotiff = []
        #
        # Iterar a través de los archivos en el directorio y seleccionar los archivos GeoTIFF
        for archivo in os.listdir():
            if archivo.endswith('.tif'):
                archivos_geotiff.append(archivo)
        #
        # Leer y sumar los archivos GeoTIFF
        suma_geotiff = None
        for archivo in archivos_geotiff:
            with rasterio.open(archivo) as src:
                if suma_geotiff is None:
                    suma_geotiff = src.read(1)
                else:
                    try:
                        suma_geotiff += src.read(1)
                    except:
                        print(f"No se pudo sumar un valor en archivo {archivo}")
        #
        # Factor de conversion de a mm/h es 0.1 (como los datos son cada media hora de debe dividir para 2)
        suma_geotiff = suma_geotiff*0.05
        #
        # Crear una copia de uno de los archivos GeoTIFF para obtener los metadatos
        with rasterio.open(archivos_geotiff[0]) as src:
            perfil = src.profile
            perfil.update(count=1)
        #
        # Guardar el resultado en un nuevo archivo GeoTIFF
        with rasterio.open('pacum.tif', 'w', **perfil) as dst:
            dst.write(suma_geotiff, 1)
        #
        # Definir coordenadas geográficas del rectángulo de recorte (minx, miny, maxx, maxy)
        minx, miny, maxx, maxy = (-92.5, -5.5, -74.5, 1.65)
        #minx, miny, maxx, maxy = (-95, -7, -70, 4)
        #
        # Crear una geometría de rectángulo
        bbox = box(minx, miny, maxx, maxy)
        #
        # Crear un GeoDataFrame con la geometría del rectángulo
        gdf = gpd.GeoDataFrame({'geometry': [bbox]}, crs=from_epsg(4326))
        #
        with rasterio.open("pacum.tif") as src:
            out_image, out_transform = rasterio.mask.mask(src, gdf.geometry, crop=True)
            out_meta = src.meta
        #
        out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform})
        #
        with rasterio.open("pacum_masked.tif", "w", **out_meta) as dest:
            dest.write(out_image)
        #
        outpath = f"/home/ubuntu/data/report/pacum_{temp}.tif"
        if os.path.exists(outpath):
            os.remove(outpath)
        os.system("gdalwarp -tr 0.01 0.01 -r bilinear pacum_masked.tif pacum_masked_res.tif")
        os.system(f"gdalwarp -q -cutline ~/tethys_apps_ecuador/geoglows_database_ecuador/shp/nwsaffgs_ecuador_basins_v2.shp -tr 0.01 0.01 -of GTiff pacum_masked_res.tif {outpath}")
    except Exception as e:
        print("Ocurred an error!")
        print(e)
    # Revome the files
    for f in os.listdir():
        os.remove(f)

get_imerg_pacum(24)
get_imerg_pacum(72)

##################################################################################################
##################################################################################################
##################################################################################################

# Import libraries and dependencies
import os
import ssl
import datetime
import urllib.request
import gzip
import shutil
from dotenv import load_dotenv
import geopandas as gpd
import pandas as pd
from hsclient import HydroShare


# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("tethys_apps_ecuador/geoglows_database_ecuador")

# Import enviromental variables
load_dotenv()
NWSAFFGS_USER = os.getenv('NWSAFFGS_USER')
NWSAFFGS_PASS = os.getenv('NWSAFFGS_PASS')
HS_USER = os.getenv('HS_USER')
HS_PASS = os.getenv('HS_PASS')
HS_IDRS = os.getenv('HS_ID02')
PYTHON_PATH = os.getenv('PYTHON_PATH')


# Retieve the actual hour
actual_date = datetime.datetime.now() + datetime.timedelta(hours=-5)
hora_actual = actual_date.hour
run_hour = "00"

# Determine the run hour
if 0 <= hora_actual < 6:
    run_hour = "00"
elif 6 <= hora_actual < 12:
    run_hour = "06"
elif 12 <= hora_actual < 18:
    run_hour = "12"
else:
    run_hour = "18"

print(run_hour)


# Read the shapefile
shapefile_path = 'shp/nwsaffgs_ecuador_basins_v2.shp'
gdf_shapefile = gpd.read_file(shapefile_path)


# Define the function to retrieve data from the server
def get_file(product, filename, run, colname):
    # Change the work directory
    os.chdir(user_dir)
    os.chdir("data/nwsaffgs")
    #
    # Generate the actual date
    actual_date = datetime.datetime.now() + datetime.timedelta(hours=-5)
    actual_year = actual_date.strftime("%Y")
    actual_month = actual_date.strftime("%m")
    actual_day = actual_date.strftime("%d")
    actual_hour = run
    print(actual_date)
    #
    # URL for the comprimed file (*.gz)
    url = "https://nwsaffgs-ubuntu.hrcwater.org/NWSAFFGS_CONSOLE/EXPORTS/REGIONAL/{0}/{1}/{2}/{4}_TXT/{0}{1}{2}-{3}00_ffgs_prod_{5}_regional.txt.gz"
    url = url.format(actual_year, actual_month, actual_day, actual_hour, product, filename)
    # Download the *.gz file
    gz_filename = "data.gz"
    os.system(f"wget --user {NWSAFFGS_USER} --password {NWSAFFGS_PASS} --no-check-certificate {url} -O {gz_filename}")
    # Tar the *.gz file
    output_filename = "data.txt"  # Nombre del archivo descomprimido
    with gzip.open(gz_filename, 'rb') as gz_file, open(output_filename, 'wb') as out_file:
        shutil.copyfileobj(gz_file, out_file)
    print("Download successfully completed!")
    # Read the file and join
    data_nwsaffgs = pd.read_table("data.txt", sep="\t")
    data_nwsaffgs.columns = ["BASIN", colname]
    return(data_nwsaffgs)



# Humedad Promedio del Suelo (ASM)
asm = get_file(product = "ASM", filename = "est_asm_sacsma_06hr", run = run_hour, colname="asm")

# Precipitacion crítica para crecida (FFG)
ffg = get_file(product = "FFG", filename = "est_ffg_smffg_06hr", run = run_hour, colname="ffg")

# Pronostico de precipitacion WRF proximas 6 horas
fmap06 = get_file(product = "FMAP2", filename = "fcst_map_forecast2_06hr", run = run_hour, colname="fmap06")

# Pronostico de precipitacion WRF proximas 24 horas
fmap24 = get_file(product = "FMAP2", filename = "fcst_map_forecast2_24hr", run = run_hour, colname="fmap24")

# Pronostico de riesgo de crecidas repentinas proximas 12 horas
ffr12 = get_file(product = "FFR2", filename = "fcst_ffr_outlook2_12hr", run = run_hour, colname="ffr12")

# Pronostico de riesgo de crecidas repentinas proximas 24 horas
ffr24 = get_file(product = "FFR2", filename = "fcst_ffr_outlook2_24hr", run = run_hour, colname="ffr24")


# Merge data
nwsaffds_data = pd.merge(asm, ffg, on="BASIN", how="outer")
nwsaffds_data = pd.merge(nwsaffds_data, fmap06, on="BASIN", how="outer")
nwsaffds_data = pd.merge(nwsaffds_data, fmap24, on="BASIN", how="outer")
nwsaffds_data = pd.merge(nwsaffds_data, ffr12, on="BASIN", how="outer")
nwsaffds_data = pd.merge(nwsaffds_data, ffr24, on="BASIN", how="outer")

# Combine data with shapefile
gdf_merged = gdf_shapefile.merge(nwsaffds_data, left_on='BASIN', right_on='BASIN', how='left')


# Save the new shapefile
output_shapefile_path = '/home/ubuntu/data/report/nwsaffds.shp'
gdf_merged.to_file(output_shapefile_path)
print("Merged data!")







####################################################################################################
####################################################################################################
####################################################################################################
# Import libraries and dependencies
import os
import math
import psycopg2
import requests
import geoglows
import datetime
import warnings
import rasterio
import rasterio.mask
from rasterio.mask import mask
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox


from io import BytesIO
from rasterio.plot import show
from hs_restclient import HydroShare, HydroShareAuthBasic
from matplotlib.colors import ListedColormap
from sqlalchemy import create_engine
from dotenv import load_dotenv
import cairosvg


warnings.filterwarnings('ignore')


# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("tethys_apps_ecuador/geoglows_database_ecuador")

# Import enviromental variables
load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
HS_USER = os.getenv('HS_USER')
HS_PASS = os.getenv('HS_PASS')
HS_IDRS = os.getenv('HS_ID02')

# Generate the conection token
token = "postgresql+psycopg2://{0}:{1}@localhost:5432/{2}".format(DB_USER, DB_PASS, DB_NAME)



###############################################################################################################
#                                                   COLORBARS                                                 #
###############################################################################################################
def rgba_to_hex(rgba_color):
    r, g, b, a = rgba_color
    r = int(r)
    g = int(g)
    b = int(b)
    a = int(a)
    hex_color = "#{:02X}{:02X}{:02X}".format(r, g, b)
    return hex_color

def color_pacum(pixelValue):
    if pixelValue == 0:
        return "none"
    elif 0.01 <= pixelValue <= 0.5:
        return rgba_to_hex((180, 215, 255, 255))
    elif 0.5 < pixelValue <= 1:
        return rgba_to_hex((117, 186, 255, 255))
    elif 1 < pixelValue <= 2:
        return rgba_to_hex((53, 154, 255, 255))
    elif 2 < pixelValue <= 3:
        return rgba_to_hex((4, 130, 255, 255))
    elif 3 < pixelValue <= 4:
        return rgba_to_hex((0, 105, 255, 255))
    elif 4 < pixelValue <= 5:
        return rgba_to_hex((0, 54, 127, 255))
    elif 5 < pixelValue <= 7:
        return rgba_to_hex((20, 143, 27, 255))
    elif 7 < pixelValue <= 10:
        return rgba_to_hex((26, 207, 5, 255))
    elif 10 < pixelValue <= 15:
        return rgba_to_hex((99, 237, 7, 255))
    elif 15 < pixelValue <= 20:
        return rgba_to_hex((255, 244, 43, 255))
    elif 20 < pixelValue <= 25:
        return rgba_to_hex((232, 220, 0, 255))
    elif 25 < pixelValue <= 30:
        return rgba_to_hex((240, 96, 0, 255))
    elif 30 < pixelValue <= 35:
        return rgba_to_hex((255, 127, 39, 255))
    elif 35 < pixelValue <= 40:
        return rgba_to_hex((255, 166, 106, 255))
    elif 40 < pixelValue <= 45:
        return rgba_to_hex((248, 78, 120, 255))
    elif 45 < pixelValue <= 50:
        return rgba_to_hex((247, 30, 84, 255))
    elif 50 < pixelValue <= 60:
        return rgba_to_hex((191, 0, 0, 255))
    elif 60 < pixelValue <= 70:
        return rgba_to_hex((136, 0, 0, 255))
    elif 70 < pixelValue <= 80:
        return rgba_to_hex((100, 0, 0, 255))
    elif 80 < pixelValue <= 90:
        return rgba_to_hex((194, 0, 251, 255))
    elif 90 < pixelValue <= 100:
        return rgba_to_hex((221, 102, 255, 255))
    elif 100 < pixelValue <= 125:
        return rgba_to_hex((235, 166, 255, 255))
    elif 125 < pixelValue <= 150:
        return rgba_to_hex((249, 230, 255, 255))
    elif 150 < pixelValue <= 300:
        return rgba_to_hex((212, 212, 212, 255))
    elif pixelValue > 300:
        return rgba_to_hex((0, 0, 0, 255))
    else:
        return "none"


def color_pacum_invert(pixelValue):
    if pixelValue == 0:
        return "none"
    elif 0.01 <= pixelValue <= 0.5:
        return rgba_to_hex((0, 0, 0, 255))
    elif 0.5 < pixelValue <= 1:
        return rgba_to_hex((212, 212, 212, 255))
    elif 1 < pixelValue <= 2:
        return rgba_to_hex((249, 230, 255, 255))
    elif 2 < pixelValue <= 3:
        return rgba_to_hex((235, 166, 255, 255))
    elif 3 < pixelValue <= 4:
        return rgba_to_hex((221, 102, 255, 255))
    elif 4 < pixelValue <= 5:
        return rgba_to_hex((194, 0, 251, 255))
    elif 5 < pixelValue <= 7:
        return rgba_to_hex((100, 0, 0, 255))
    elif 7 < pixelValue <= 10:
        return rgba_to_hex((136, 0, 0, 255))
    elif 10 < pixelValue <= 15:
        return rgba_to_hex((191, 0, 0, 255))
    elif 15 < pixelValue <= 20:
        return rgba_to_hex((247, 30, 84, 255))
    elif 20 < pixelValue <= 25:
        return rgba_to_hex((248, 78, 120, 255))
    elif 25 < pixelValue <= 30:
        return rgba_to_hex((255, 166, 106, 255))
    elif 30 < pixelValue <= 35:
        return rgba_to_hex((255, 127, 39, 255))
    elif 35 < pixelValue <= 40:
        return rgba_to_hex((240, 96, 0, 255))
    elif 40 < pixelValue <= 45:
        return rgba_to_hex((232, 220, 0, 255))
    elif 45 < pixelValue <= 50:
        return rgba_to_hex((255, 244, 43, 255))
    elif 50 < pixelValue <= 60:
        return rgba_to_hex((99, 237, 7, 255))
    elif 60 < pixelValue <= 70:
        return rgba_to_hex((26, 207, 5, 255))
    elif 70 < pixelValue <= 80:
        return rgba_to_hex((20, 143, 27, 255))
    elif 80 < pixelValue <= 90:
        return rgba_to_hex((0, 54, 127, 255))
    elif 90 < pixelValue <= 100:
        return rgba_to_hex((0, 105, 255, 255))
    elif 100 < pixelValue <= 125:
        return rgba_to_hex((4, 130, 255, 255))
    elif 125 < pixelValue <= 150:
        return rgba_to_hex((53, 154, 255, 255))
    elif 150 < pixelValue <= 300:
        return rgba_to_hex((117, 186, 255, 255))
    elif pixelValue > 300:
        return rgba_to_hex((180, 215, 255, 255))
    else:
        return "none"



def color_percent(pixelValue):
    if 0 <= pixelValue <= 0.1:
        return "#F9F788"
    elif 0.1 <= pixelValue <= 0.2:
        return "#D6D309"
    elif 0.2 <= pixelValue <= 0.3:
        return "#B08C00"
    elif 0.3 <= pixelValue <= 0.4:
        return "#B6F8A9"
    elif 0.4 <= pixelValue <= 0.5:
        return "#1DD41C"
    elif 0.5 <= pixelValue <= 0.6:
        return "#005200"
    elif 0.6 <= pixelValue <= 0.7:
        return "#359AFF"
    elif 0.7 <= pixelValue <= 0.8:
        return "#0069D2"
    elif 0.8 <= pixelValue <= 0.9:
        return "#00367F"
    elif 0.9 <= pixelValue <= 1:
        return "#100053"
    else:
        return "none"





###############################################################################################################
#                                                PLOT FUNCTIONS                                               #
###############################################################################################################
def get_pacum_plot(raster_url, gdf, fig_name):
    # Abre el raster utilizando rasterio
    with rasterio.open(raster_url) as src:
        # Realiza el enmascaramiento del raster con las geometrías del shapefile
        out_image, out_transform = rasterio.mask.mask(src, gdf.geometry, crop=True)
    #
    # Crear una lista de valores entre 0 y 1
    mmin = out_image.min()
    mmax = out_image.max()
    rang = 100*(mmax - mmin)
    values = np.linspace(mmin, mmax, rang)  # Asegurarse de que haya suficientes valores en el rango
    #
    # Crear una lista de colores utilizando la función color
    colors = [color_pacum(value) for value in values]
    #
    # Crear un objeto ListedColormap basado en la lista de colores
    cmap_custom = ListedColormap(colors)
    #
    # Crea una figura de Matplotlib y muestra el raster enmascarado
    plt.figure(figsize=(8, 8))
    plt.margins(0)
    show(out_image, transform=out_transform, ax=plt.gca(), cmap=cmap_custom)
    gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=1)
    #
    # Establecer límites en los ejes x e y
    plt.xlim(-81.3, -74.9)
    plt.ylim(-5.2, 1.6)
    plt.axis("off")
    #
    # Save the figure
    print("Saving image PACUM")
    fig_path = f'{user_dir}/data/report/{fig_name}'
    plt.savefig(fig_path, bbox_inches='tight', pad_inches=0)


def get_ffgs_plot(field, gdf, gdf2, umbral, colorfun):
    # Generate the color bar
    mmin = gdf[field].min()
    mmax = gdf[field].max()
    rang = umbral*(mmax - mmin)
    values = np.linspace(mmin, mmax, int(rang))  
    #
    # Crear una lista de colores utilizando la función color
    colors = [colorfun(value) for value in values]
    #
    # Crear un objeto ListedColormap basado en la lista de colores
    cmap_custom = ListedColormap(colors)
    #
    # Crea una figura de Matplotlib y muestra el raster enmascarado
    plt.figure(figsize=(8, 8))
    plt.margins(0)
    #
    # Graficar el GeoDataFrame utilizando el campo especificado
    gdf.plot(column=field, legend=False, cmap=cmap_custom, figsize=(8, 8))
    gdf2.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=1)
    #
    # Establecer límites en los ejes x e y
    plt.xlim(-81.3, -74.9)
    plt.ylim(-5.2, 1.6)
    plt.axis("off")
    #
    # Save the figure
    print("Saving image FFGS")
    fig_path = f'{user_dir}/data/report/fig_{field}.png'
    plt.savefig(fig_path, bbox_inches='tight', pad_inches=0)



def get_geoglows(gdf, gdf2, df): #gdf -> ecuador, gdf2 -> drainage, df -> alerts
    # Crear una figura y ejes de Matplotlib
    fig, ax = plt.subplots(figsize=(8, 8))
    #
    # Graficar el archivo SHP
    gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=1)
    gdf2.plot(ax=ax, color='blue', edgecolor='blue', linewidth=0.3)
    #
    # Configurar la ruta a los archivos SVG para cada clase 'alert'
    svg_mapping = {
        'R0': 'svg/0.svg',
        'R2': 'svg/2.svg',
        'R5': 'svg/5.svg',
        'R10': 'svg/10.svg',
        'R25': 'svg/25.svg',
        'R50': 'svg/50.svg',
        'R100': 'svg/100.svg'
    }
    #
    # Graficar los puntos utilizando archivos SVG como marcadores
    for index, row in df.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        alert = row['alert']
        #   
        # Obtener la ruta del archivo SVG correspondiente
        svg_path = svg_mapping.get(alert, 'default_icon.svg')
        #
        # Convertir el archivo SVG en una imagen temporal (PNG)
        temp_png_path = 'temp_icon.png'
        cairosvg.svg2png(url=svg_path, write_to=temp_png_path)
        #
        # Cargar la imagen PNG como un OffsetImage
        img = OffsetImage(plt.imread(temp_png_path), zoom=0.5)
        ab = AnnotationBbox(img, (lon, lat), frameon=False)
        #
        # Agregar el marcador al gráfico
        ax.add_artist(ab)
    #
    # Establecer límites en los ejes x e y para delimitar la figura
    plt.xlim(-81.3, -74.9)
    plt.ylim(-5.2, 1.6)
    plt.axis("off")
    plt.margins(0)
    #
    # Save the figure
    print("Saving image GEOGLOWS")
    fig_path = f'{user_dir}/data/report/fig_geoglows.png'
    plt.savefig(fig_path, bbox_inches='tight', pad_inches=0)



###############################################################################################################
#                                               STATS FUNCTIONS                                               #
###############################################################################################################

def get_pacum_stats(raster_url, gdf):
  # Crear listas para almacenar los valores máximos y mínimos
  max_values = []
  min_values = []
  # Abrir el archivo raster con rasterio
  with rasterio.open(raster_url) as src:
      for idx, row in gdf.iterrows():
          # Obtener la geometría de la feature
          geom = row['geometry']
          # Recortar el área correspondiente en el raster
          out_image, out_transform = mask(src, [geom], crop=True)
          # Calcular el valor máximo y mínimo en el área recortada
          max_val = np.nanmax(out_image)
          min_val = np.nanmin(out_image)
          # Agregar los valores a las listas
          max_values.append(max_val)
          min_values.append(min_val)
  # Agregar las listas como nuevas columnas en el GeoDataFrame
  gdf['max'] = max_values
  gdf['min'] = min_values
  xmax = gdf[["DPA_VALOR", "max"]].groupby('DPA_VALOR').max()
  xmin = gdf[["DPA_VALOR", "min"]].groupby('DPA_VALOR').min()
  pmax = "max"
  pmin = "min"
  out_text = [
    f"entre {xmin[pmin][1]} y {xmax[pmax][1]} mm",
    f"entre {xmin[pmin][2]} y {xmax[pmax][2]} mm",
    f"entre {xmin[pmin][3]} y {xmax[pmax][3]} mm"]
  return(out_text)


def get_threshold(param, unit, factor, xmax, xmin):
  out = [
    f"entre {round(factor*xmin[param][1],1)} y {round(factor*xmax[param][1],1)} {unit}" ,
    f"entre {round(factor*xmin[param][2],1)} y {round(factor*xmax[param][2],1)} {unit}" ,
    f"entre {round(factor*xmin[param][3],1)} y {round(factor*xmax[param][3],1)} {unit}"
  ]
  return(out)






###############################################################################################################
#                                                MAIN FUNCTIONS                                               #
###############################################################################################################

# Get Ecuador boundaries
ecu = gpd.read_file("shp/ecuador.shp")
print("Read Ecuador Boundaries")

# Get drainage
drainage = gpd.read_file("shp/drainage.shp")
print("Read Ecuador Drainage")

# Get FFGS data
shp_url = "/home/ubuntu/data/report/nwsaffds.shp"
ffgs = gpd.read_file(shp_url)
print("Read FFGS data")

# Pacum raster URL
raster_url = "/home/ubuntu/data/report/pacum_24.tif"
raster_url_72 = "/home/ubuntu/data/report/pacum_72.tif"

# Get data from DB
db = create_engine(token)
conn = db.connect()
alerts = pd.read_sql("select loc1, latitude,longitude,alert from drainage_network where alert != 'R0' and loc1 != 'GALAPAGOS';", conn)
conn.close()
print("Retrieved data from DB")


# Generate figures
get_pacum_plot(raster_url = raster_url, gdf = ecu, fig_name="fig_pacum.png")
get_pacum_plot(raster_url = raster_url_72, gdf = ecu, fig_name="fig_pacum_72.png")

get_ffgs_plot(field="asm", gdf=ffgs, gdf2=ecu, umbral=10, colorfun=color_percent)
get_ffgs_plot(field="ffg", gdf=ffgs, gdf2=ecu, umbral=100, colorfun=color_pacum_invert)
get_ffgs_plot(field="fmap24", gdf=ffgs, gdf2=ecu, umbral=100, colorfun=color_pacum)
get_ffgs_plot(field="ffr24", gdf=ffgs, gdf2=ecu, umbral=10, colorfun=color_percent)
get_geoglows(gdf=ecu, gdf2=drainage, df=alerts)

# Getting stats
union = gpd.overlay(ffgs, ecu, how='intersection') 
union = union[['asm', 'ffg', 'fmap06', 'fmap24', 'ffr12', 'ffr24', 'DPA_VALOR', "DPA_DESPRO"]]
union = union.replace(-999, np.nan)
xmin = union.groupby('DPA_VALOR').min()
xmax = union.groupby('DPA_VALOR').max()

# Getting provinces
maxprov = union.groupby('DPA_DESPRO').max()
maxprov["loc1"] = maxprov.index
maxprov = maxprov[maxprov['ffr24'] > 0.3][["loc1","DPA_VALOR"]]
aleprov = alerts["loc1"].drop_duplicates().to_frame(name='loc1')
combined = pd.merge(maxprov, aleprov, how='inner', left_on='loc1', right_on='loc1')
combined['loc1'] = combined['loc1'].str.title()

# Getting string per region
co = combined[combined["DPA_VALOR"] == 1]["loc1"].str.cat(sep=', ')
si = combined[combined["DPA_VALOR"] == 2]["loc1"].str.cat(sep=', ')
am = combined[combined["DPA_VALOR"] == 3]["loc1"].str.cat(sep=', ')


data = {
    "region": ["costa", "sierra", "amazonia"],
    "pacum": get_pacum_stats(raster_url, ecu), 
    "asm": get_threshold("asm", "%", 100, xmax, xmin),
    "ffg": get_threshold("ffg", "mm", 1, xmax, xmin),
    "fmap24": get_threshold("fmap24", "mm", 1, xmax, xmin),
    "ffr24": get_threshold("ffr24", "%", 100, xmax, xmin),
    "prov": [
        co if co != "" else "Sin alertas", 
        si if si != "" else "Sin alertas", 
        am if am != "" else "Sin alertas"
    ]
}


df = pd.DataFrame(data)
print("Generating stats")



# Establish connection
db = create_engine(token)
conn = db.connect()
df.to_sql('ffgs_stats', con=conn, if_exists='replace', index=False)
# Close connection
conn.close()
print("Uploaded stats")  







################################################################################################
################################################################################################
################################################################################################
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send(subject, body, attachment_files, sender, password):
    # Users to send email
    recipients = [
        "prediccion@inamhi.gob.ec",
        "jusethchancay@ecociencia.org"]
    #
    # SMTP server
    smtp_server = "smtp.office365.com"
    smtp_port = 587
    #
    # Configure the message
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = ", ".join(recipients)
    message['Subject'] = subject
    #
    # Attach the email body
    message.attach(MIMEText(body, 'plain'))
    #
    # Attach the PDF file
    for attachment_file in attachment_files:
        attachment = open(attachment_file, 'rb')
        attachment_part = MIMEBase('application', 'octet-stream')
        attachment_part.set_payload((attachment).read())
        encoders.encode_base64(attachment_part)
        attachment_part.add_header('Content-Disposition', "attachment; filename= %s" % attachment_file)
        message.attach(attachment_part)
    #
    # Connect to the SMTP server and send the email
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, recipients, message.as_string())
    server.quit()




# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("tethys_apps_ecuador/geoglows_database_ecuador")

# Load enviromental variables - credentials
load_dotenv()
MAIL_USER = os.getenv('MAIL_USER')
MAIL_PASS = os.getenv('MAIL_PASS')

subject = "Graficas actualizadas FFGS y precipitacion satelital"
body = "Estimad@s,\n\nDesde la plataforma INAMHI GEOGLOWS se adjuntan las graficas actualizadas de FFGS y precipitacion satelital, para su uso en productos generados por la DPA.\n\nArchivos adjuntos:\n\n1. Humedad del suelo\n2. Pronóstico precipitación prox. 12 horas\n3. Alertas crecidas repentinas FFGS\n4. Alertas crecidas repentinas GEOGLOWS\n5. Precipitación acumulada últimas 24 horas\n6. Precipitación acumulada últimas 72 horas. \n\nSaludos Cordiales,\nINAMHI GEOGLOWS"
attachment_files = [
    "/home/ubuntu/data/report/fig_asm.png",
    "/home/ubuntu/data/report/fig_ffg.png",
    "/home/ubuntu/data/report/fig_ffr24.png",
    "/home/ubuntu/data/report/fig_geoglows.png",
    "/home/ubuntu/data/report/fig_pacum.png",
    "/home/ubuntu/data/report/fig_pacum_72.png"
]
send(subject, body, attachment_files, MAIL_USER, MAIL_PASS)
