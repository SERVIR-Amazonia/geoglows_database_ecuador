import os
import mail
import plot
import imerg
import report
import warnings
import rgeoglows
import cgeoglows
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
paute = gpd.read_file("shp/paute.shp")
prov = gpd.read_file("shp/ecuador.shp")
ec = gpd.read_file("shp/ecuador_diss.shp")
rp = gpd.read_file("shp/rios_principales.shp")
rs = gpd.read_file("shp/rios_secundarios.shp")
embalses = gpd.read_file("shp/embalses.shp")
subcuencas = gpd.read_file("shp/paute_subcuencas_2.shp")
print("Read SHP files")

# Read Paute data
h0894 = pd.read_csv("H0894-paute.dat", sep="\t", header=0)
h0894.index = h0894.datetime
h0894 = h0894.drop(columns=['datetime'])
h0894.index = pd.to_datetime(h0894.index)
h0894.index = h0894.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
h0894.index = pd.to_datetime(h0894.index)
print("Read observed data - H0894")

# Load enviromental variables - credentials
load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
MAIL_USER = os.getenv('MAIL_USER')
MAIL_PASS = os.getenv('MAIL_PASS')
print("Read enviromental variables")

# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("data/paute")

# Download data
imerg.get(outpath="../paute_final/imerg.tif")
print("Downloaded IMERG data")

# Change the work directory
os.chdir("../paute_final")

# Compute mean precipitation per subbasin
pacum_subbasins = imerg.get_pacum_subbasin("imerg.tif", subcuencas, "SC")
pacum_subbasins = pacum_subbasins.reindex([0,2,1,3,4])
pacum_subbasins = pacum_subbasins.rename(columns={'subbasin': 'Subcuenca', 'pacum': 'Precipitación media diaria (mm)'})
pacum_basin = imerg.get_pacum_subbasin("imerg.tif", paute, "Subcuenca")
print("Computed mean precipitation")


# Generate precipitation plots
plot.pacum_ec(raster="imerg.tif", ec_gdf=ec, prov_gdf=prov, paute_gdf=paute)
plot.pacum_paute(raster="imerg.tif", paute_gdf=paute, rp_gdf=rp, rs_gdf=rs, embalses_gdf=embalses)
plot.join_images("ecuador.png", "paute.png")
os.remove("ecuador.png")
os.remove("paute.png")
print("Generated precipitation plots")


# Establish connection
token = "postgresql+psycopg2://{0}:{1}@localhost:5432/{2}".format(DB_USER, DB_PASS, DB_NAME)
db = create_engine(token)
conn = db.connect()

# Generate data and plot for river basins
paute_table = cgeoglows.plot(9033441, h0894, conn, "paute.png")
cuenca_table = rgeoglows.plot(9033449, conn, "cuenca.png")
gualaceo_table = rgeoglows.plot(9033577, conn, "gualaceo.png")
mazar_table = rgeoglows.plot(9032447, conn, "mazar.png")
juval_table = rgeoglows.plot(9032294, conn, "juval.png")
palmira_table = rgeoglows.plot(9032324, conn, "palmira.png")
print("Generated streamflow forecast plots")

# Close connection
conn.close()

# Generate report
filename = dt.datetime.now().strftime('boletin-paute_%Y-%m-%d.pdf')
report.report(
    filename, 
    pacum=pacum_basin.pacum[0], 
    pacum_table=pacum_subbasins,
    paute_table=paute_table,
    cuenca_table = cuenca_table,
    gualaceo_table = gualaceo_table,
    mazar_table = mazar_table,
    juval_table = juval_table,
    palmira_table = palmira_table)
print("Generated PDF report")

# Send email
mail.send(
    subject=dt.datetime.now().strftime('Boletin Hidrometeorológico Paute %Y-%m-%d'),
    body="La DIRECCIÓN DE PRONÓSTICOS Y ALERTAS HIDROMETEOROLÓGICAS DEL INAMHI, basándose en la información obtenida de la plataforma INAMHI GEOGLOWS emite el siguiente boletín de vigilancia y predicción de condiciones hidrometeorológicas en la Cuenca del río Paute.",
    attachment_file=filename,
    sender=MAIL_USER,
    password=MAIL_PASS
)
print("Sent email")