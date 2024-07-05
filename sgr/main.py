import utils
import report
import os
import plot
import imerg
import warnings
import subprocess
import pandas as pd
import datetime as dt
import geopandas as gpd
from dotenv import load_dotenv
from sqlalchemy import create_engine




# Ignore warnings
warnings.filterwarnings("ignore")

# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("tethys_apps_ecuador/geoglows_database_ecuador")

# Read SHP files
ec = gpd.read_file("shp/ecuador_diss.shp")
prov = gpd.read_file("shp/ecuador.shp")
area = gpd.read_file("shp/area_afectada.shp")
rios_principales = gpd.read_file("shp/rios_principales_banos.shp")
rios_secundarios = gpd.read_file("shp/rios_secundarios_banos.shp")
puntos_afectados = gpd.read_file("shp/puntos_afectados.shp")




os.chdir(user_dir)
os.chdir("data/sgr")

if os.path.exists("pacumres.tif"): os.remove("pacumres.tif")
if os.path.exists("wrfres.tif"): os.remove("wrfres.tif")

# Datos satelitales
url = "https://www.hydroshare.org/resource/925ad37f78674d578eab2494e13db240/data/contents/pacum_persiann_daily7.tif"
os.system(f"wget {url} -O pacum.tif")
os.system("gdalwarp -tr 0.01 0.01 -r bilinear pacum.tif pacumres.tif")
plot.pacum_ec(raster="pacumres.tif", ec_gdf=ec, prov_gdf=prov, paute_gdf=area)
plot.pacum_area(raster="pacumres.tif", ec_gdf=ec, rp_gdf=rios_principales, rs_gdf=rios_secundarios, puntos_gdf=puntos_afectados)
plot.join_images("ecuador.png", "area.png", "pacum_sat.png")
pacum_satellite = plot.get_pacum_subbasin("pacumres.tif", area, "id").pacum[0]


# Pronóstico
now = dt.datetime.now()
layers = utils.get_layer_wrf_name(now)
while len(layers)<=0:
    now = now - dt.timedelta(days=1)
    layers = utils.get_layer_wrf_name(now)
url = "http://ec2-3-211-227-44.compute-1.amazonaws.com:4200/wrf-precipitation"
url = f"{url}/{layers[0]}/{layers[0]}.geotiff"
os.system(f"wget {url} -O wrf.tif")
os.system("gdalwarp -tr 0.01 0.01 -r bilinear wrf.tif wrfres.tif")
plot.pacum_ec(raster="wrfres.tif", ec_gdf=ec, prov_gdf=prov, paute_gdf=area)
plot.pacum_area(raster="wrfres.tif", ec_gdf=ec, rp_gdf=rios_principales, rs_gdf=rios_secundarios, puntos_gdf=puntos_afectados)
plot.join_images("ecuador.png", "area.png", "pacum_wrf.png")
pacum_wrf = plot.get_pacum_subbasin("wrfres.tif", area, "id").pacum[0]


# Humedad del suelo
#os.system("gdal_rasterize -a asm -tr 0.01 0.01 -l nwsaffds /home/ubuntu/data/nwsaffgs/nwsaffds.shp soilmoisture.tif")
ffgs = gpd.read_file("/home/ubuntu/data/nwsaffgs/nwsaffds.shp")
plot.get_asm_plot(ffgs, prov_gdf=prov, ec_gdf=ec, area_gdf=area)




report.report(filename="prueba.pdf", pacum=pacum_satellite, forecast=pacum_wrf)
