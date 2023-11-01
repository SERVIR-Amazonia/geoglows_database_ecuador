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
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


from io import BytesIO
from rasterio.plot import show
from hs_restclient import HydroShare, HydroShareAuthBasic
from matplotlib.colors import ListedColormap
from sqlalchemy import create_engine
from dotenv import load_dotenv

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
def get_pacum_plot(raster_url, gdf):
    # Realiza una solicitud HTTP para obtener el contenido del archivo Raster
    raster_response = requests.get(raster_url)

    # Verifica si la solicitud fue exitosa
    if raster_response.status_code == 200:
        # Lee el contenido de la respuesta en un objeto BytesIO
        raster_data = BytesIO(raster_response.content)
        print("Read pacum data")

        # Abre el raster utilizando rasterio
        with rasterio.open(raster_data) as src:
            # Realiza el enmascaramiento del raster con las geometrías del shapefile
            out_image, out_transform = rasterio.mask.mask(src, gdf.geometry, crop=True)

        # Crear una lista de valores entre 0 y 1
        mmin = out_image.min()
        mmax = out_image.max()
        rang = 100*(mmax - mmin)
        values = np.linspace(mmin, mmax, rang)  # Asegurarse de que haya suficientes valores en el rango

        # Crear una lista de colores utilizando la función color
        colors = [color_pacum(value) for value in values]

        # Crear un objeto ListedColormap basado en la lista de colores
        cmap_custom = ListedColormap(colors)

        # Crea una figura de Matplotlib y muestra el raster enmascarado
        plt.figure(figsize=(8, 8))
        plt.margins(0)
        show(out_image, transform=out_transform, ax=plt.gca(), cmap=cmap_custom)
        gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=1)

        # Establecer límites en los ejes x e y
        plt.xlim(-81.3, -74.9)
        plt.ylim(-5.2, 1.6)
        plt.axis("off")

        # Save the figure
        print("Saving image PACUM")
        fig_path = f'{user_dir}/data/report/fig_pacum.png'
        plt.savefig(fig_path, bbox_inches='tight', pad_inches=0)

    else:
        print("Error al descargar el archivo Raster. Código de estado:", raster_response.status_code)


def get_ffgs_plot(field, gdf, gdf2, umbral, colorfun):
    # Generate the color bar
    mmin = gdf[field].min()
    mmax = gdf[field].max()
    rang = umbral*(mmax - mmin)
    values = np.linspace(mmin, mmax, int(rang))  

    # Crear una lista de colores utilizando la función color
    colors = [colorfun(value) for value in values]

    # Crear un objeto ListedColormap basado en la lista de colores
    cmap_custom = ListedColormap(colors)

    # Crea una figura de Matplotlib y muestra el raster enmascarado
    plt.figure(figsize=(8, 8))
    plt.margins(0)

    # Graficar el GeoDataFrame utilizando el campo especificado
    gdf.plot(column=field, legend=False, cmap=cmap_custom, figsize=(8, 8))
    gdf2.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=1)

    # Establecer límites en los ejes x e y
    plt.xlim(-81.3, -74.9)
    plt.ylim(-5.2, 1.6)
    plt.axis("off")

    # Save the figure
    print("Saving image FFGS")
    fig_path = f'{user_dir}/data/report/fig_{field}.png'
    plt.savefig(fig_path, bbox_inches='tight', pad_inches=0)



###############################################################################################################
#                                                MAIN FUNCTIONS                                               #
###############################################################################################################

# Get Ecuador boundaries
ecu = gpd.read_file("shp/ecuador.shp")
print("Read Ecuador Boundaries")

# Get FFGS data
shp_url = "https://geoserver.hydroshare.org/geoserver/HS-352379cf82444fd099eca8bfc662789b/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=nwsaffds&maxFeatures=20000&outputFormat=application/json"
ffgs = gpd.read_file(shp_url)
print("Read FFGS data")

# Pacum raster URL
raster_url = "https://www.hydroshare.org/resource/925ad37f78674d578eab2494e13db240/data/contents/pacum_24_res.tif"

# Generate figures
get_pacum_plot(raster_url = raster_url, gdf = ecu)
get_ffgs_plot(field="asm", gdf=ffgs, gdf2=ecu, umbral=10, colorfun=color_percent)
get_ffgs_plot(field="ffg", gdf=ffgs, gdf2=ecu, umbral=100, colorfun=color_pacum)
get_ffgs_plot(field="fmap24", gdf=ffgs, gdf2=ecu, umbral=100, colorfun=color_pacum)
get_ffgs_plot(field="ffr24", gdf=ffgs, gdf2=ecu, umbral=10, colorfun=color_percent)




auth = HydroShareAuthBasic(username=HS_USER, password=HS_PASS)
hs = HydroShare(auth=auth)

def upload_file(hs, local_file, resource_filename):
    try:
        hs.deleteResourceFile(HS_IDRS,  resource_filename)
    except:
        print("File was not found in resource")
    hs.addResourceFile(HS_IDRS, local_file, resource_filename)


upload_file(hs, f'{user_dir}/data/report/fig_pacum.png', "fig_pacum.png")
upload_file(hs, f'{user_dir}/data/report/fig_asm.png', "fig_asm.png")
upload_file(hs, f'{user_dir}/data/report/fig_ffg.png', "fig_ffg.png")
upload_file(hs, f'{user_dir}/data/report/fig_fmap24.png', "fig_fmap24.png")
upload_file(hs, f'{user_dir}/data/report/fig_ffr24.png', "fig_ffr24.png")


