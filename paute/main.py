import os
import plot
import imerg
import report
import warnings
import rgeoglows
import cgeoglows
import pandas as pd
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
paute = gpd.read_file("shp/paute.shp")
prov = gpd.read_file("shp/ecuador.shp")
ec = gpd.read_file("shp/ecuador_diss.shp")
rp = gpd.read_file("shp/rios_principales.shp")
rs = gpd.read_file("shp/rios_secundarios.shp")
embalses = gpd.read_file("shp/embalses.shp")
subcuencas = gpd.read_file("shp/paute_subcuencas_2.shp")
print("Reading SHP files")

# Read Paute data
h0894 = pd.read_csv("H0894-paute.dat", sep="\t", header=0)
h0894.index = h0894.datetime
h0894 = h0894.drop(columns=['datetime'])
h0894.index = pd.to_datetime(h0894.index)
h0894.index = h0894.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
h0894.index = pd.to_datetime(h0894.index)

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

# Compute mean precipitation per subbasin
pacum_subbasins = imerg.get_pacum_subbasin("imerg.tif", subcuencas, "SC")
pacum_subbasins = pacum_subbasins.reindex([0,2,1,3,4])
pacum_subbasins = pacum_subbasins.rename(columns={'subbasin': 'Subcuenca', 'pacum': 'Precipitación media diaria (mm)'})
pacum_basin = imerg.get_pacum_subbasin("imerg.tif", paute, "Subcuenca")


# Generate precipitation plots
plot.pacum_ec(raster="imerg.tif", ec_gdf=ec, prov_gdf=prov, paute_gdf=paute)
plot.pacum_paute(raster="imerg.tif", paute_gdf=paute, rp_gdf=rp, rs_gdf=rs, embalses_gdf=embalses)
plot.join_images("ecuador.png", "paute.png")

# Remove indivual plot
os.remove("ecuador.png")
os.remove("paute.png")


# Establish connection
db = create_engine(token)
conn = db.connect()

# Rio Paute (en Paute)
comid = 9033441
paute_table = cgeoglows.plot(comid, h0894, conn, "paute_en_paute.png")

# Close connection
conn.close()


filename = "report.pdf"
report.report(
    filename, 
    pacum=pacum_basin.pacum[0], 
    pacum_table=pacum_subbasins,
    paute_table=paute_table)

