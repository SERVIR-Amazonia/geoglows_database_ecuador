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



def get_geoglows(gdf, gdf2, df): #gdf -> ecuador, gdf2 -> drainage, df -> alerts
    # Crear una figura y ejes de Matplotlib
    fig, ax = plt.subplots(figsize=(8, 8))

    # Graficar el archivo SHP
    gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=1)
    gdf2.plot(ax=ax, color='blue', edgecolor='blue', linewidth=0.3)

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

    # Graficar los puntos utilizando archivos SVG como marcadores
    for index, row in df.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        alert = row['alert']
        
        # Obtener la ruta del archivo SVG correspondiente
        svg_path = svg_mapping.get(alert, 'default_icon.svg')
        
        # Convertir el archivo SVG en una imagen temporal (PNG)
        temp_png_path = 'temp_icon.png'
        cairosvg.svg2png(url=svg_path, write_to=temp_png_path)
        
        # Cargar la imagen PNG como un OffsetImage
        img = OffsetImage(plt.imread(temp_png_path), zoom=0.5)
        ab = AnnotationBbox(img, (lon, lat), frameon=False)
        
        # Agregar el marcador al gráfico
        ax.add_artist(ab)

    # Establecer límites en los ejes x e y para delimitar la figura
    plt.xlim(-81.3, -74.9)
    plt.ylim(-5.2, 1.6)
    plt.axis("off")
    plt.margins(0)

    # Save the figure
    print("Saving image GEOGLOWS")
    fig_path = f'{user_dir}/data/report/fig_geoglows.png'
    plt.savefig(fig_path, bbox_inches='tight', pad_inches=0)



###############################################################################################################
#                                               STATS FUNCTIONS                                               #
###############################################################################################################

def get_pacum_stats(raster_url, gdf):
  # Realiza una solicitud HTTP para obtener el contenido del archivo Raster
  raster_response = requests.get(raster_url)
  raster_data = BytesIO(raster_response.content)
  # Crear listas para almacenar los valores máximos y mínimos
  max_values = []
  min_values = []
  # Abrir el archivo raster con rasterio
  with rasterio.open(raster_data) as src:
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
shp_url = "https://geoserver.hydroshare.org/geoserver/HS-352379cf82444fd099eca8bfc662789b/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=nwsaffds&maxFeatures=20000&outputFormat=application/json"
ffgs = gpd.read_file(shp_url)
print("Read FFGS data")

# Pacum raster URL
raster_url = "https://www.hydroshare.org/resource/925ad37f78674d578eab2494e13db240/data/contents/pacum_24_res.tif"

# Get data from DB
db = create_engine(token)
conn = db.connect()
alerts = pd.read_sql("select loc1, latitude,longitude,alert from drainage_network where alert != 'R0' and loc1 != 'GALAPAGOS';", conn)
conn.close()
print("Retrieved data from DB")


# Generate figures
get_pacum_plot(raster_url = raster_url, gdf = ecu)
get_ffgs_plot(field="asm", gdf=ffgs, gdf2=ecu, umbral=10, colorfun=color_percent)
get_ffgs_plot(field="ffg", gdf=ffgs, gdf2=ecu, umbral=100, colorfun=color_pacum)
get_ffgs_plot(field="fmap24", gdf=ffgs, gdf2=ecu, umbral=100, colorfun=color_pacum)
get_ffgs_plot(field="ffr24", gdf=ffgs, gdf2=ecu, umbral=10, colorfun=color_percent)
get_geoglows(gdf=ecu, gdf2=drainage, df=alerts)

# Upload data to hydroshare
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
upload_file(hs, f'{user_dir}/data/report/fig_geoglows.png', "fig_geoglows.png")
print("Uploaded data")


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




