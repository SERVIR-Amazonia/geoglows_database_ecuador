import os
import plot
import imerg
import rgeoglows
import geopandas as gpd
from dotenv import load_dotenv
from sqlalchemy import create_engine


# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("tethys_apps_ecuador/geoglows_database_ecuador")

# Read SHP files
paute = gpd.read_file("shp/paute.shp")
prov = gpd.read_file("shp/ecuador.shp")
ec = gpd.read_file("shp/ecuador_diss.shp")
rp = gpd.read_file("shp/rios_principales.shp")
rs = gpd.read_file("shp/rios_secundarios.shp")
embalses = gpd.read_file("shp/embalses.shp")
subcuencas = gpd.read_file("shp/paute_subcuencas_2.shp")
print("Reading SHP files")

# Generate the conection token
load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
token = "postgresql+psycopg2://{0}:{1}@localhost:5432/{2}".format(DB_USER, DB_PASS, DB_NAME)

# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("data/paute")

# Download data
imerg.get(outpath="../paute_final/imerg.tif")

# Change the work directory
os.chdir("../paute_final")

pacum_subbasins = imerg.get_pacum_subbasin("imerg.tif", subcuencas, "SC")
pacum_basin = imerg.get_pacum_subbasin("imerg.tif", paute, "Subcuenca")

print(pacum_subbasins)
print(pacum_basin)


# Generate precipitation plots
#plot.pacum_ec(raster="imerg.tif", ec_gdf=ec, prov_gdf=prov, paute_gdf=paute)
#plot.pacum_paute(raster="imerg.tif", paute_gdf=paute, rp_gdf=rp, rs_gdf=rs, embalses_gdf=embalses)

# Establish connection
#db = create_engine(token)
#conn = db.connect()

#comid = 9033441
#a = rgeoglows.plot(comid, conn, "prueba.png")

# Close connection
#conn.close()

