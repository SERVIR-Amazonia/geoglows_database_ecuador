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


# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("data/gpm_imerg")


def get_imerg_pacum(temp):
    try:
        if(temp == 24):
            ndays = 1
        elif(temp == 48):
            ndays = 2
        else:
            ndays = 3
        #
        # Generar la fecha actual
        actual_date = datetime.datetime.now() + datetime.timedelta(hours=-5)
        actual_year = actual_date.strftime("%Y")
        actual_month = actual_date.strftime("%m")
        #
        # Descargar los nombres de archivos existentes
        url = "https://jsimpsonhttps.pps.eosdis.nasa.gov/text/imerg/gis/early/{0}/{1}/"
        url = url.format(actual_year, actual_month)
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
                source = "/imerg/gis/early/{0}/{1}/3B-HHR-E.MS.MRG.3IMERG.{0}{1}{2}-S{3}{4}{5}-E{6}{7}{8}".format(start_year,start_month,start_day,start_hour,start_minute,start_second,finish_hour,finish_minute,finish_second)
                resultado = files[files['files'].str.contains(source)]
                resultado = resultado[resultado['files'].str.contains(".V06D.30min.tif")].iloc[0,0]
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
            except:
                print("Conexion no permitida")
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
        os.system("gdalwarp -tr 0.01 0.01 -r bilinear pacum_masked.tif pacum_masked_res.tif")
        os.system("gdalwarp -q -cutline ~/tethys_apps_ecuador/geoglows_database_ecuador/shp/nwsaffgs_ecuador_basins_v2.shp -tr 0.01 0.01 -of GTiff pacum_masked_res.tif pacum_masked_res2.tif")
        #
        auth = HydroShareAuthBasic(username=HS_USER, password=HS_PASS)
        hs = HydroShare(auth=auth)
        local_file = "pacum_masked_res2.tif"
        resource_filename = f"pacum_{temp}_res.tif"
        hs.deleteResourceFile(HS_IDRS,  resource_filename)
        hs.addResourceFile(HS_IDRS, local_file, resource_filename)
        hs.resource(HS_IDRS).public(True)
        hs.resource(HS_IDRS).shareable(True)
        #
    except:
        print("Ocurred an error!")
    # Revome the files
    for f in os.listdir():
        os.remove(f)




get_imerg_pacum(24)
get_imerg_pacum(48)
get_imerg_pacum(72)

# gdalwarp -q -cutline ~/tethys_apps_ecuador/geoglows_database_ecuador/shp/nwsaffgs_ecuador_basins_v2.shp -tr 0.01 0.01 -of GTiff pacum_masked.tif pacum_masked_res.tif