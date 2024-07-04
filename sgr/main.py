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
rios_secundarios = gpd.read_file("shp/rios_secundarion_banos.shp")




os.chdir(user_dir)
os.chdir("data/sgr")

url = "https://www.hydroshare.org/resource/925ad37f78674d578eab2494e13db240/data/contents/pacum_persiann_daily7.tif"
os.system(f"wget {url} -O pacum.tif")
os.system("gdalwarp -tr 0.01 0.01 -r bilinear pacum.tif pacumres.tif")
plot.pacum_ec(raster="pacumres.tif", ec_gdf=ec, prov_gdf=prov, paute_gdf=area)
plot.pacum_area(raster="pacumres.tif", area_gdf=area)

